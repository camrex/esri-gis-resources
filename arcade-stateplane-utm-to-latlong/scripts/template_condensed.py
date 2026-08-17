"""The condensed Arcade template, used by build_expression.py --style condensed.

Same program as the documented template and the same substitutions, with the
commentary and long identifiers stripped. It exists only for pasting into a small
dialog: the two run within 0.3% of each other, so the documented one is the version
to read and to edit first.

Data blocks marked @@LIKE_THIS@@ are substituted by the generator; the maths between
them is fixed. @@ELL_SELECT@@ is either a constant 0, a WKID range test, or an index
unpacked from the run value, depending on how many ellipsoids the chosen codes use.

Arcade identifiers are CASE-INSENSITIVE. `U` and `u` are the same variable. Every
name below is deliberately distinct case-insensitively; run lint.py after editing.
"""

CONDENSED = r'''@@HEADER@@
var MD="LAT";
var FMT="#.######";
var LF="@@LAT_FIELD@@";
var NF="@@LON_FIELD@@";
var FV=null;
var GW=@@GW@@;
var KS=@@KS@@;
var FE=@@FE@@;
var FN=@@FN@@;
var UT=@@UT@@;
var ZN=[
@@ZN@@
];
var RN=[
@@RN@@
];
function ecn(ax,fi){
 var fl=1.0/fi;
 var e2=2*fl-fl*fl;
 var n3=fl/(2-fl);
 return [e2,Sqrt(e2),e2/(1-e2),ax/(1+n3)*(1+Pow(n3,2)/4+Pow(n3,4)/64),
  -3*n3/2+9*Pow(n3,3)/16,15*Pow(n3,2)/16-15*Pow(n3,4)/32,-35*Pow(n3,3)/48,315*Pow(n3,4)/512,
  3*n3/2-27*Pow(n3,3)/32,21*Pow(n3,2)/16-55*Pow(n3,4)/32,151*Pow(n3,3)/96,1097*Pow(n3,4)/512,
  e2/2+5*Pow(e2,2)/24+Pow(e2,3)/12+13*Pow(e2,4)/360,
  7*Pow(e2,2)/48+29*Pow(e2,3)/240+811*Pow(e2,4)/11520,
  7*Pow(e2,3)/120+81*Pow(e2,4)/1120,4279*Pow(e2,4)/161280,ax];
}
var EL=@@EL@@;
function rd(dv){ return dv*PI/180.0; }
function dg(rv){ return rv*180.0/PI; }
function ma(ph,es){ return es[3]*(ph+es[4]*Sin(2*ph)+es[5]*Sin(4*ph)+es[6]*Sin(6*ph)+es[7]*Sin(8*ph)); }
function fpr(mu,es){ return mu+es[8]*Sin(2*mu)+es[9]*Sin(4*mu)+es[10]*Sin(6*mu)+es[11]*Sin(8*mu); }
function cpr(ch,es){ return ch+es[12]*Sin(2*ch)+es[13]*Sin(4*ch)+es[14]*Sin(6*ch)+es[15]*Sin(8*ch); }
function tfn(ph,es){ return Tan(PI/4-ph/2)/Pow((1-es[1]*Sin(ph))/(1+es[1]*Sin(ph)),es[1]/2); }
function mfn(ph,es){ return Cos(ph)/Sqrt(1-es[0]*Pow(Sin(ph),2)); }
function bad(ms){ if(MD=="RULE"){ return {"errorMessage":ms}; } return FV; }
function iTM(xx,yy,zr,es){
 var k0=zr[3];
 var mu=(yy-zr[6]+k0*ma(rd(zr[1]),es))/(k0*es[3]);
 var ph=fpr(mu,es);
 var qq=(xx-zr[5])/(k0*es[16]/Sqrt(1-es[0]*Pow(Sin(ph),2)));
 var q2=qq*qq;
 var tn=Tan(ph);
 var t2=tn*tn;
 var t4=t2*t2;
 var et=es[2]*Pow(Cos(ph),2);
 var b2=-0.5*tn*(1+et);
 var b4=-(1.0/12.0)*(5+3*t2+et*(1-9*t2)-4*et*et);
 var b6=(1.0/360.0)*(61+90*t2+45*t4+et*(46-252*t2-90*t4));
 var b3=-(1.0/6.0)*(1+2*t2+et);
 var b5=(1.0/120.0)*(5+28*t2+24*t4+et*(6+8*t2));
 var b7=-(1.0/5040.0)*(61+662*t2+1320*t4+720*t2*t4);
 var ph2=ph+b2*q2*(1+q2*(b4+b6*q2));
 var lm=rd(zr[2])+qq*(1+q2*(b3+q2*(b5+b7*q2)))/Cos(ph);
 return [dg(ph2),dg(lm)];
}
function iLC(xx,yy,zr,es){
 var s1=rd(zr[3]);
 var s2=rd(zr[4]);
 var t1=tfn(s1,es);
 var t2=tfn(s2,es);
 var nn=0;
 if(Abs(s1-s2)<0.000000000001){ nn=Sin(s1); } else { nn=(Log(mfn(s1,es))-Log(mfn(s2,es)))/(Log(t1)-Log(t2)); }
 var fk=mfn(s1,es)/(nn*Pow(t1,nn));
 var r0=es[16]*fk*Pow(tfn(rd(zr[1]),es),nn);
 var dx=xx-zr[5];
 var dy=r0-(yy-zr[6]);
 var sg=IIf(nn>0,1.0,-1.0);
 var tt=Pow(sg*Sqrt(dx*dx+dy*dy)/(es[16]*fk),1.0/nn);
 return [dg(cpr(PI/2-2*Atan(tt),es)),dg(rd(zr[2])+Atan2(sg*dx,sg*dy)/nn)];
}
function iHO(xx,yy,zr,es){
 var e2=es[0];
 var pc=rd(zr[1]);
 var kc=zr[4];
 var sn=Sin(pc);
 var bb=Sqrt(1+e2*Pow(Cos(pc),4)/(1-e2));
 var ab=es[16]*bb*kc*Sqrt(1-e2)/(1-e2*sn*sn);
 var dd=bb*Sqrt(1-e2)/(Cos(pc)*Sqrt(1-e2*sn*sn));
 var fk=dd+Sqrt(Max(dd*dd,1.0)-1)*IIf(pc>=0,1.0,-1.0);
 var hh=fk*Pow(tfn(pc,es),bb);
 var gg=(fk-1/fk)/2;
 var ga=Asin(Sin(rd(zr[3]))/dd);
 var lc=rd(zr[2])-Asin(gg*Tan(ga))/bb;
 var rg=rd(zr[7]);
 var de=xx-zr[5];
 var dn=yy-zr[6];
 var vv=de*Cos(rg)-dn*Sin(rg);
 var uu=dn*Cos(rg)+de*Sin(rg);
 var qq=Exp(-(bb*vv)/ab);
 var ss=(qq-1/qq)/2;
 var tt=(qq+1/qq)/2;
 var vs=Sin(bb*uu/ab);
 var us=(vs*Cos(ga)+ss*Sin(ga))/tt;
 var tp=Pow(hh/Sqrt((1+us)/(1-us)),1.0/bb);
 return [dg(cpr(PI/2-2*Atan(tp),es)),dg(lc-Atan2(ss*Cos(ga)-vs*Sin(ga),Cos(bb*uu/ab))/bb)];
}
var gm=Geometry($feature);
if(IsEmpty(gm)){ return bad("No geometry."); }
var ky=Text(gm.spatialReference.wkid);
var wn=Number(ky);
var ct=Centroid(gm);
var ll=[0,0];
if(Includes(GW,wn)){
 ll=[ct.Y,ct.X];
} else {
 var pk=-1;
 for(var i=0;i<Count(RN);i++){
  var rr=RN[i];
  var dd=wn-rr[0];
  if(dd>=0 && dd<=rr[3]*(rr[1]-1) && dd%rr[3]==0){ pk=rr[2]+(dd/rr[3])*rr[4]; break; }
 }
 if(pk<0){ return bad("WKID "+ky+" is not a supported coordinate system for this build."); }
 var zi=Floor(pk/@@STRIDE@@);
 var es=EL[@@ELL_SELECT@@];
 var um=UT[pk-Floor(pk/@@UNIT_MOD@@)*@@UNIT_MOD@@];
 var zc=ZN[zi];
 var zz=[zc[0],zc[1]/3600,zc[2]/3600,0,0,FE[zc[5]],FN[zc[6]],zc[7]/3600];
 if(zc[0]==0){ zz[3]=KS[zc[3]]; }
 else if(zc[0]==1){ zz[3]=zc[3]/3600; zz[4]=zc[4]/3600; }
 else { zz[3]=zc[3]; zz[4]=KS[zc[4]]; zz[7]=zc[7]; }
 var xm=ct.X*um;
 var ym=ct.Y*um;
 if(zz[0]==0){ ll=iTM(xm,ym,zz,es); } else if(zz[0]==1){ ll=iLC(xm,ym,zz,es); } else { ll=iHO(xm,ym,zz,es); }
}
var la=Round(ll[0],9);
var lr=ll[1];
if(lr>180){ lr=lr-360; }
if(lr<-180){ lr=lr+360; }
var lo=Round(lr,9);
if(IsNan(la)||IsNan(lo)||Abs(la)>90||Abs(lo)>180){ return bad("Inverse projection failed for WKID "+ky+"."); }
if(MD=="LAT"){ return la; }
if(MD=="LON"){ return lo; }
if(MD=="BOTH"){ return "Lat: "+Text(la,FMT)+", Lon: "+Text(lo,FMT); }
return {"result":{"attributes":Dictionary(LF,la,NF,lo)}};
'''
