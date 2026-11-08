import asyncio, json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
from playwright.async_api import async_playwright
JS = r'''
(data)=>{
 const PAD=192,GF='"Noto Sans Gujarati",sans-serif';
 const mc=document.createElement('canvas').getContext('2d');
 const lay=g=>{mc.font='500 100px '+GF;const m=mc.measureText(g),L=m.actualBoundingBoxLeft,R=m.actualBoundingBoxRight,A=m.actualBoundingBoxAscent,D=m.actualBoundingBoxDescent;const k=Math.min(130/(L+R||1),130/(A+D||1),1.7);return{size:100*k,x:PAD/2-(R-L)*k/2,y:PAD/2+(A-D)*k/2}};
 const ks=Object.keys(data),cols=8,T=200,c=document.createElement('canvas');c.width=cols*T;c.height=Math.ceil(ks.length/cols)*T;
 const x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);
 const C=['#e6194b','#3cb44b','#4363d8','#f58231','#911eb4','#42d4f4','#f032e6'];
 ks.forEach((g,i)=>{x.save();x.translate((i%cols)*T+4,Math.floor(i/cols)*T+4);
  x.fillStyle='#f3edd6';x.fillRect(0,0,PAD,PAD);const l=lay(g);x.fillStyle='#cfc4a0';x.font=`500 ${l.size}px ${GF}`;x.fillText(g,l.x,l.y);
  data[g].forEach((s,k)=>{x.strokeStyle=C[k%7];x.lineWidth=3;x.lineCap=x.lineJoin='round';x.beginPath();x.moveTo(s[0][0],s[0][1]);s.forEach(p=>x.lineTo(p[0],p[1]));if(s.length===1)x.lineTo(s[0][0]+.1,s[0][1]);x.stroke();
   if(s.length>2){const a=s.at(-1),b=s[Math.max(0,s.length-4)],an=Math.atan2(a[1]-b[1],a[0]-b[0]);x.fillStyle=C[k%7];x.beginPath();x.moveTo(a[0]+Math.cos(an)*6,a[1]+Math.sin(an)*6);x.lineTo(a[0]+Math.cos(an+2.4)*6,a[1]+Math.sin(an+2.4)*6);x.lineTo(a[0]+Math.cos(an-2.4)*6,a[1]+Math.sin(an-2.4)*6);x.fill()}
   x.fillStyle=C[k%7];x.beginPath();x.arc(s[0][0],s[0][1],7,0,7);x.fill();x.fillStyle='#fff';x.font='bold 10px Arial';x.textAlign='center';x.textBaseline='middle';x.fillText(k+1,s[0][0],s[0][1]+.5);x.textAlign='left';x.textBaseline='alphabetic'});
  x.fillStyle='#000';x.font='bold 14px Arial';x.fillText(i+1,4,16);x.restore()});
 return c.toDataURL('image/png');
}'''
async def main():
    data=json.load(open(sys.argv[1]))
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--allow-file-access-from-files'])
        pg=await b.new_page()
        css = os.environ.get('FONTS_CSS')  # optional: serve fonts locally when Google Fonts is unreachable
        if css: await pg.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(path=css, content_type='text/css'))
        await pg.goto('file://'+os.path.join(HERE,'fit.html'));await pg.evaluate('document.fonts.load(\'500 100px "Noto Sans Gujarati"\',"અક")');await pg.wait_for_timeout(300)
        url=await pg.evaluate(JS,data);await b.close()
    import base64;open(sys.argv[2],'wb').write(base64.b64decode(url.split(',')[1]))
asyncio.run(main())
