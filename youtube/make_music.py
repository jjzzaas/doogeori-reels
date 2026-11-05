import numpy as np, wave
import sys
SR=44100; DUR=float(sys.argv[2]) if len(sys.argv)>2 else 15.0; N=int(SR*DUR)
bpm=98; beat=60/bpm
def midi(m): return 440*2**((m-69)/12)
def tone(f,dur,amp=1.0,kind='ep'):
    n=int(dur*SR); t=np.arange(n)/SR
    if kind=='ep':
        s=np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*2*f*t)*np.exp(-t*5)+0.12*np.sin(2*np.pi*3*f*t)*np.exp(-t*8)
        env=np.minimum(t/0.006,1)*np.exp(-t*2.6)
    elif kind=='pad':
        s=np.sin(2*np.pi*f*t)+np.sin(2*np.pi*f*1.003*t)*0.8+0.3*np.sin(2*np.pi*2*f*t)
        env=np.minimum(t/0.9,1)*np.minimum((dur-t)/0.9,1)
    else: # bass
        s=np.sin(2*np.pi*f*t)+0.2*np.sin(2*np.pi*2*f*t)
        env=np.minimum(t/0.01,1)*np.exp(-t*1.8)
    return s*env*amp
mix=np.zeros(N)
def add(sig,start):
    i=int(start*SR); e=min(N,i+len(sig))
    if i<N: mix[i:e]+=sig[:e-i]
bar=beat*4
# C - Am - F - G - C
chords=[([60,64,67,71],36),([57,60,64,67],33),([53,57,60,64],29),([55,59,62,64],31),([60,64,67,71],36)]
b=0
while b*bar<DUR:
    notes,root=chords[b%4]
    t0=b*bar; b+=1
    L=min(bar,DUR-t0)+0.8
    for n in notes: add(tone(midi(n-12),L,0.10,'pad'),t0)
    add(tone(midi(root+12),bar*0.98,0.22,'bass'),t0)
    add(tone(midi(root+12),bar*0.5,0.14,'bass'),t0+beat*2.5)
    # gentle arpeggio, eighth notes
    pat=[0,1,2,3,2,1,2,1]
    for k,pi in enumerate(pat):
        tt=t0+k*beat/2
        if tt<DUR-0.3:
            add(tone(midi(notes[pi]+12*(1 if pi==3 else 0)),1.6,0.17 if k%2==0 else 0.12,'ep'),tt)
# light shaker + soft kick for energy
rs=np.random.RandomState(7)
t=0.0
while t<DUR-0.2:
    n=int(0.05*SR); nz=rs.randn(n)*np.exp(-np.arange(n)/SR*55)*0.05
    add(nz,t+beat/2)
    add(nz*0.7,t)
    t+=beat
tk=0.0
while tk<DUR-0.5:
    n=int(0.18*SR); tt=np.arange(n)/SR
    add(np.sin(2*np.pi*(50+90*np.exp(-tt*30))*tt)*np.exp(-tt*16)*0.20,tk)
    tk+=beat*2
# soft reverb
ir_n=int(SR*1.6); ir=np.random.RandomState(1).randn(ir_n)*np.exp(-np.arange(ir_n)/SR*3.2)
ir/=np.sqrt((ir**2).sum())
from scipy.signal import fftconvolve, butter, lfilter
wet=fftconvolve(mix,ir)[:N]
sig=mix*0.75+wet*0.45
b,a=butter(2,5500/(SR/2),'low'); sig=lfilter(b,a,sig)
fade_in=np.minimum(np.arange(N)/(SR*0.4),1); fade_out=np.minimum((N-np.arange(N))/(SR*1.2),1)
sig*=fade_in*fade_out
sig/=np.abs(sig).max(); sig*=0.8
st=np.stack([sig,np.roll(sig,int(SR*0.012))],1)
pcm=(st*32767).astype(np.int16)
w=wave.open(__import__('sys').argv[1] if len(__import__('sys').argv)>1 else 'music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok')
