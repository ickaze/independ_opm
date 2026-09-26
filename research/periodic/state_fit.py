# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from analyze import *
v=load('42STATE');rows=[]
# Unwrap AM saw attenuation only within each local fitting window.
def fit(a,b,at):
 m=(v['t']>a)&(v['t']<b);t=v['t'][m];d=v['db'][m]
 d=np.unwrap(d/(.09409*254)*2*np.pi)/(2*np.pi)*(.09409*254)
 p=np.polyfit(t-at,d,1);return float(p[0]),float(p[1]),float(np.sqrt(np.mean((np.polyval(p,t-at)-d)**2)))
for j in range(0,len(v['ss']),4):
 ss=v['ss'][j:j+4];label=ss[0]['label'];kind=label.split()[1]
 a=v['offset']+v['scale']*ss[2]['start_s'];b=v['offset']+v['scale']*ss[3]['start_s']
 pre=fit(a-.25,a-.02,a);post=fit(b+.025,b+.25,b)
 during=(v['t']>a+.004)&(v['t']<b-.004)
 rows.append(dict(label=label,kind=kind,frequency=ss[0]['registers']['18'],event_s=a,release_s=b,pre_slope_db_s=pre[0],post_slope_db_s=post[0],pre_level_at_event_db=pre[1],post_level_at_release_db=post[1],continuity_residual_db=post[1]-(pre[1]+pre[0]*(b-a)),during_median_db=float(np.median(v['db'][during])) if during.any() else None,pre_rms_db=pre[2],post_rms_db=post[2]))
(R/'state_fit.json').write_text(json.dumps(rows,indent=2))
for kind in ['same_freq','new_freq','hold','wave_select']:
 rr=[r for r in rows if r['kind']==kind];print(kind,'n',len(rr),'continuity quantiles',np.quantile([r['continuity_residual_db'] for r in rr],[0,.5,1]),'postlevel',np.quantile([r['post_level_at_release_db'] for r in rr],[0,.5,1]))
