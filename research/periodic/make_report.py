# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from analyze import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from measurement_model import am_units
am=json.loads((R/'am_fixed.json').read_text());pm=json.loads((R/'pm_endpoint127.json').read_text());bad=json.loads((R/'pm_fit.json').read_text());state=json.loads((R/'state_fit.json').read_text());overview=json.loads((R/'overview.json').read_text());inputs=json.loads((R/'inputs.json').read_text());native=json.loads((R/'native_check.json').read_text());steps=json.loads((R/'state_steps.json').read_text())
fig,ax=plt.subplots(2,2,figsize=(13,8),layout='constrained')
for name,shape,color in [('37AMSAW',0,'tab:blue'),('39AMTRI',2,'tab:orange')]:
 v=load(name);t,d,c=section(v,v['ss'][-1]);r=next(r for r in am['rows'] if r['file']==name[:2] and r['amd']==127)
 i=np.floor((t-r['offset_s'])/am['step_s']).astype(int);pred=np.array([am_units(shape,int(j),127) for j in i])*am['unit_db']
 ax[0,0].plot(t[::5],d[::5],color=color,label=name+' measured',lw=1)
 ax[0,0].plot(t[::5],pred[::5],color='black',alpha=.4,lw=.5)
ax[0,0].axvspan(4.3,5.9,color='green',alpha=.1);ax[0,0].set(xlabel='Seconds within section',ylabel='Attenuation (dB)',title='AM: measured and integer candidate, AMD127');ax[0,0].legend(fontsize=8)
for k,label in [('37','Saw'),('38','Square'),('39','Triangle')]:
 r=[r for r in am['rows'] if r['file']==k];ax[0,1].plot([r['amd'] for r in r],[r['test_rms_db'] for r in r],label=label)
ax[0,1].set(xlabel='AMD',ylabel='RMS error (dB)',title='AM held-time-window error');ax[0,1].legend()
for z,style,label in [(bad,'--','-128 endpoint'),(pm,'-','-127 endpoint')]:
 for k,col in [('40','tab:blue'),('41','tab:orange')]:
  yy=[max(r['test_rms_cents'] for r in z['rows'] if r['file']==k and r['pms']==p) for p in range(8)]
  ax[1,0].plot(range(8),yy,style,color=col,label=k+' '+label)
ax[1,0].set(xlabel='PMS',ylabel='Maximum section RMS (cent)',title='PM endpoint candidate comparison');ax[1,0].legend(fontsize=8)
r=[r for r in state if r['kind']=='wave_select'];x=np.array([r['pre_slope_db_s']*(r['release_s']-r['event_s']) for r in r]);y=np.array([r['continuity_residual_db'] for r in r]);ax[1,1].scatter(x,y,label='24 trials');ax[1,1].plot([-3,0],[-3,0],color='black',label='one extra advance rate');ax[1,1].set(xlabel='One extra rate x switch duration (dB)',ylabel='Measured extra phase equivalent (dB)',title='Triangle switch advances shared position');ax[1,1].legend(fontsize=8)
fig.savefig(R/'verification.png',dpi=160);plt.close(fig)
summary=dict(am=[],pm=[],coverage=[],native_checks=len(native))
for k in ['37','38','39']:
 r=[r for r in am['rows'] if r['file']==k];summary['am'].append(dict(file=k,conditions=len(r),points=sum(r['test_n'] for r in r),wrong_half_unit=sum(r['test_wrong_unit'] for r in r),median_section_rms_db=float(np.median([r['test_rms_db'] for r in r])),max_section_rms_db=max(r['test_rms_db'] for r in r)))
for k in ['40','41']:
 r=[r for r in pm['rows'] if r['file']==k];summary['pm'].append(dict(file=k,conditions=len(r),points=sum(r['known_pitch_n'] for r in r),unmapped=sum(r['test_n']-r['known_pitch_n'] for r in r),median_section_rms_cents=float(np.median([r['test_rms_cents'] for r in r])),max_section_rms_cents=max(r['test_rms_cents'] for r in r)))
for r,inp in zip(overview,inputs):summary['coverage'].append(dict(file=r['name'],recorded_s=float(inp['format']['duration']),active_s=r['active'][1]-r['active'][0],sections=r['sections'],scale=r['scale']))
(R/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
