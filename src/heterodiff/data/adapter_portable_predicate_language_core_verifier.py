"""Implementation-separated verifier for the portable semantic core.

The verifier loads an embedded frozen canonical descriptor without importing
the source-core module, checks its known answers, independently validates the
closed profile interface, and emits a nonclaiming static result.  It is not a
runtime predicate evaluator or a formal proof of the shared specification.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Final
import zlib


PORTABLE_PREDICATE_LANGUAGE_CORE_VERIFIER_STATUS: Final = (
    "IMPLEMENTATION_SEPARATED_STATIC_CORE_VERIFIER_IMPLEMENTED"
)
_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-semantic-core-contract.v1"
)
_PROFILE_INTERFACE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-profile-interface.v1"
)
_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-core-verification-result.v1"
)
_VERIFIER_ID: Final = (
    "heterodiff.adapter.portable-predicate-language-core-frozen-verifier.v1"
)
_ENCODING_ID: Final = "canonical-ascii-json-sort-keys-no-whitespace-v1"
_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)
_V1_BYTE_COUNT: Final = 57674
_V1_PLAIN_SHA256: Final = (
    "b13e1d349c08449096bd901e46087bbcc44181365354b553e6ecd89172864dc2"
)
_V1_SHA256: Final = (
    "387b45d6f4ae8485433b36b929ed4d3a7b146c61e5d12629d46e2a74aa4536b2"
)
_V1_INTERFACE_SHA256: Final = (
    "2698f51d7326cc89d7a90880a7feea59d4cab81b3fffd4d04bc995ae646464b2"
)
_V1_RESULT_BYTE_COUNT: Final = 775
_V1_RESULT_PLAIN_SHA256: Final = (
    "c0c6bf7caa1331f8e766599b487328ba6557c57146b1d74da3a11fa8b7d559f9"
)
_V1_RESULT_SHA256: Final = (
    "84565f9f6fa4248bb089389a03f333ac580b3fb655bc7cae93072f4e7833a931"
)
_LOCATOR_PRIMITIVE_IDS: Final = (
    "bounded-artifact-path",
    "direct-bound-value",
    "ordered-index",
    "composite-key",
    "sibling-resolved-value",
)
_PURPOSE_RELATION_PRIMITIVE_IDS: Final = (
    "exactly-one-pinned-anchor-row-canonical-equality-v1",
    "purpose-identifiers-exactly-covered-by-input-locators-v1",
)
_REQUIRED_PROFILE_PARAMETER_SLOT_IDS: Final = (
    "primary-program-purpose-id",
)
_REQUIRED_PUBLIC_ERROR_ROLE_IDS: Final = (
    "LOCAL_RULE_FAILED",
    "RUNTIME_SOURCE_UNAVAILABLE",
    "PARSER_REJECTED",
    "DERIVATION_MISMATCH",
    "UPSTREAM_RULE_FAILED",
    "EXTERNAL_AUTHORITY_UNAVAILABLE",
    "STATIC_MAPPING_UNRESOLVED",
)
_REQUIRED_RUNTIME_ARTIFACT_ROLE_IDS: Final = (
    "predicate-program",
    "predicate-evaluation-context",
    "predicate-input-bundle",
    "predicate-evaluation-result",
    "predicate-formula-core",
)
_RESERVED_METADATA_ARTIFACT_ROLE_IDS: Final = (
    "semantic-core-contract",
    "selected-profile-contract",
)
_PROFILE_FIELD_VALUE_SCHEMA_IDS: Final = (
    "strict-identifier-string-v1",
    "lowercase-sha256-string-v1",
    "nonnegative-index-or-count-integer-v1",
    "ordered-identifier-array-v1",
    "ordered-exact-object-row-array-v1",
)
_PROFILE_FIELD_SEMANTIC_ROLE_IDS: Final = (
    "opaque-identifier",
    "artifact-type-for-role",
    "artifact-identity-semantics-for-role",
    "artifact-identity-sha256-for-role",
    "anchor-artifact-type-for-role",
    "anchor-contract-sha256-for-role",
    "ordered-unique-identifiers",
    "identifier-member-of-purpose-field",
    "locator-kind-self",
    "path-segments",
    "nonnegative-count",
    "index-below-field",
    "typed-key-components",
    "prior-input-resolved-operand",
)
_MAX_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
_MAX_JSON_DEPTH: Final = 32
_MAX_JSON_ITEMS: Final = 65536
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$")
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")

_COMPRESSED_CONTRACT_B85: Final = (
    b'c-rkf+jiSVlK-N|T_I~Jj^pT!k!hQ|5~-!A?09E%a3B(r5Q6{*0BtLC{O?=0z5xyJB2rd1ez8TM(Oq3#U0qdOmwz2ZMU~t}(<;1;=1KYx7WwD$;N<WBYP?8h'
    b'2PX#?MLbKUQ59bl`CSpse>*xjG%brfjk(=IwF?&95SmSkyez}pBu;1HrzlNkQI+IbSS;xy9Q5Ee`4Z0p>?Wul7IAQ!7xSnJrg;$uQ8vTQZWDO9NU}2cgkvw3'
    b'#Ud}`;3mmtNp=^+UjUGxjMI2p#pZ)@dLPdt{scQ+rV;m=l)*I0@(h4Y6|DIG@9;f9$6rLLc?b9*P(I%yl<;VAAK(<q03OV^{X8!2VDPen8BPP}eVRteycFQ@'
    b'YwYnhN&#^A;QH`@-Ux047aFUG2?0B*!cTEg0$}i<gc)TpK!_88f3m8;=H-2K{L?E$4bR>4Mlir1CbJlNsUDmUajLkI=7%6!9?B2FIy}jXSqy7Vz%mV)XZa#7'
    b'VAA!+FdnSqU6|#w#wVJ7oVP`uSNwpWP>2l?(J`V?&&8~uqAwsyUNW=X3d6zYq=H3^r}=!bw5ev6&!Z#@T!N7yc%`$rtZ*tsUTWnu8P#Z$30Ch6r(1c)9}?{&'
    b'q1`+LAK_#7t)NpiDD!18jXmuIzX2kQ8ar<d9PWER?b2^1)~|=Fc*9$s*eT3wHGi<NurDUT`_9?tYJcaqL7v4ygI{g4@t=GjKmDfLevfr+m*>1A)}Z%35bBcX'
    b'^c0pT{!*=``dEJwO!=F=9gs3R&9|UEpkEzE4!Ogk{Sg<r0*Q8iTsyDKY4$BBUY$nzfq)tksNsG5WtZndJI(HZOAazPY<^v4vvdtEnPB7KhFb5NQt+*!06|;='
    b'^g?u_L>PfpzC;en5aOnR&8U9GWuATlFw_Qx!<3lKpF>P)5S!Vxp`yE{^rW~cp+GUwCm>0iL=-2S#V~4tbbu?dG!pF&=+|()aa=Cb&6r+6pX{CI5lTF?%oN5H'
    b'ttpsc(j=@pp~C<OS06TpfbnPy2=)@NjWgtalcLCrfZm$fOZW7ljcxiSeSm4DDG*B&OC)7Hj}5>y%`~><won2H&#heqao>{=B9BP+rw8$uc!~mh7$d^17YRU7'
    b'WKoLn%o2i(UMjs1C>ndpi{viJ)Ozf3Zz{pVBC(n>P=BK}Sb{WQNJW}$5J+S5URyg+Po{`(0mpbuY8_t@63l89m6#Qkh9!UZW^~>g48zO*MQ_}j^xuS+?|b}('
    b'9&Z+U*n;YY_puu90QrsuRXc6&9-f-XpbexI%JZ(_YSEOMc&hExy@8<&IyDH^Vgmbv$|F$M0QB>&{Xyi2Y|f5!S%lt<P2OH(_^j7hoTx#wb<2Zo_R<{5kc;0!'
    b'(L9E6dFf=6v+lOY=S>@%>I^zT)IVZ6#1iPNCml{^VR)lwCVmBR^;B4ZNZ`2U9@OHNc1Ql{94Hl=juz6v=`W<jSj`T*kb_B!V8Dt0xlD?94y4EL)bSTBt9xMe'
    b'K#suD%aR5<JV<jOsJy_x5;)i3SmPm3<S0ewk>MQmp7nJfwpJ<3Ht>WvV->DJXwZrxRF!LL&<$ZVmsu6a6oX}!{BtSVy*nLih2{%oV3WC9FX7nb_u5LQgk0Wn'
    b'@`XrfZAhmD9QXhGYA}Y)J-!-F2Iu|oZEtV}U+L%lzfJn%Vec#)jwWIMx8B(m@&dxD2jAWac&Xv!U@*M6nuO#2<>>4;=#j+jR@B<~XhE3~M>IN!pcm0Ynn$xX'
    b'WLiCUqv~?fn+#6F)6sA;?ww9{fr5+i=-s$?9-a*V$-T1`I8gLsCJL0q20S>Xvl67dPm1ZPUQpEEp3wG)8xi^0@`%g_XnD4rA`5nGR9)zM(;p9jbi&Dp3-}jl'
    b'vrorN2hY>eFksK#^A;~G;*`EEJNVxJH;bmrA={0SUd(ph9?``D>#u%wHU2V9mvr<t>~!il#cv#=Tg$4{SwGpv%BomSE2SId%L-*6=iGA573Ni0>j3_~P41Qj'
    b'%^x-W#Uh1i-y|vSR_f|DO421Pcn)itb{#){JFFkQDd2$YQ3?_z4j^6t^aSlov*=E1$t~zHXrVb8oYbg`XRe-3?-S@kzAf#KcZrX-yO=JFC_ofCs(g{B`5jSW'
    b'5l7Se=myWm=uY88a3u>(%AzfMk@A?7fKp(U^CU~k3j0bQG?H)3k*m&FG4K^)Gc54DDN6Va@8~m@$bs&r`5a~!V_WPM{?pQ)xuWS1uWYDUm1lmad65yc<V{oi'
    b's7p<?)!4{@*1=^NmC<aTR28F5i(94>>loQyV76o`(tCu%G$eCv--B+OBJ?U-VCQ5Nai}B2HrTGssC;}$PCc{WK4Z_Ob{;%dW+DaD>7zysZ6=#Fa6$d!7O)p$'
    b'5#2?`o?~~Xr|C-CJWbLp%|QM0i^&IMErd|>oF*m%n-c_JNBW|k%;6ufVB;8;P^e~rJSc4rUt64$0}?;N-ftj3_kKO=^V0h!@OJPwkXFt{ryx|1ug+NHh9{$O'
    b'2=d@X?;Qx(pmm@1Pbc(r@NO_%cfLF?<V`7JU#3={y|Y7XyISYW8Ez2qE+^xw(+PkJf4><_2BTpo>~6DG{Jrmu-w-OU#vRCOALZie*E0}7`{VIwycxQ7ilxV*'
    b'!Bw-q(k;X+DM1dhM%r$NEI^&u!%onRY%r<C+34K>sT}B~Z<~58Gd3WscX_$-X7S7pMGc{Rl7sL!ESwSum?fKeZ!=>B4A1Iq@9eU_*8EjVKLSYO-aWw+KGq>^'
    b'2NQ~6?wruuvE*$0Cq`11SITZ`Hu<y0mdhX7&{gLmhu!)>+i?EwcOi(h>YN)08@C_~1{TDiFW!IxQtP74a!GJlGP4rBSl;Ck;ib4!Ag1JpBcoY5wA&*MG8_$&'
    b'q}kFny6BI4LtL}V_q~h3@Lf0@y}{QP<Nh1q6F?jEpw^Yk@RM0cV<RjULT+-<vgu)f1es)U%Ek<S0b;3T%BfBLguz5Swe-&DHXaN(4E;4@ZA}f?If#pdm80FI'
    b'`3>4=L<Z$SVL%)=j*2viOY~=3mJwOK6mTSR3N(H=9OSPHhJB~8D?n<?{<SWBw_ksD><MWGqoW?8ArReU?`l?uj<xd6wq;&<1`7BhFDlaJS&UPLDZ{!gyB;*J'
    b'3Xt*;0YLqzZnNRYXl3?Q6j|_24(?Iu&u7W)?GMo`TELGV^q^+-(<r-JMt4Z^zPsBW*tNm68SxeB$-kWE$}lpI7VHb4@1x~~L4fGVXz$<&wldq3gV6<^Bq%E>'
    b'`+e`%%l>de4$H_KL+kt$8Ko{-(WPMnirJEkJAi|a@k0j$Z>}!Rn5x+x`{;p_jL0IO0Y7!lelUbF2XDf`aMB;cpN}70HdVH2*8kQ2AO|}h<fkCf3}6)obe2C7'
    b'1hkmoZtTLj*uhx^#T%8Y@o7Ii8=Ma|TlwolFOdTMPvcq5Z$jRwTRL0D!4*Je|F(B^Hen$`e;;KZ4^Cd#Q?+`qmCMVE{^{WD;MDj1QOozEtBJZ(LJasmJ+4nu'
    b'&&V-nh8;Xsw8k4WaR-eZ&jzLFW32ZpsTbP7=MK|g!m`3>L`1%zY-k53#JvtZ1R}l9qc6#PITzz5-8cfG;dzpIpY#2K+;s@6B_os#x7;Slxv@VCmHGS|Vd$s@'
    b'Lq}_2D5>Ik0Q?z7-XE&u05GG9+Oa=``Hq|&V2?3Wp9Ukb$^$_z{oEJDl`u2p2H%F*UcKCAKPs3VYQuYkhdpo43eNm*gsC5ox7n8jaDYKf&~;Xoj4bVVK^>KQ'
    b'Ll=k$=yQM~<NlCVm&0~QXDsZZ+RS)-LP}e{dZ`7xC)lGNnQ}8c9((Z!n95L}DPZE6CO4EGvmClXhYgq~yjtWiGJB_NicwA6qKW=qf<ndUv##nuO^I9ZEqC+v'
    b'y|M<f4|HR(g*=zzSO`^XqqV7hI~-da0Xj{W^X$)zX74$qk&b+0dz7!iD11nTzsqmTYafS7^xaZ3VY=PR`NXT_pbpk+f0(Q5&0fqMZ^T>~YO=af=Ne%oI%f94'
    b'wFd+mAEz=es%Lc6Z$^G)G>-#gNej~WOES$Vk~f*cuj~%JwF+o8BLwS6AJm!`c}cU>m=UK1Wufr9go*d1ie*!cgERpIl)+7WOV-3sFnw_y65FBpNVqqo#31We'
    b'?T7U{q^7Sbd3J;@M&?OL@lTH8Lo}egk_0%*bV;OjpuP6k*GFH25Oi$&K%Ycy`nL=c|9LqYhGM9~tANw@{qvsn;Iua!4e8eKd~kW*o1DJKhvHWmz8MeRl6U1S'
    b'xr=EvFkatYVDjWpVf)#VM2?$SEv;D>@&OXZqimX^173aUqH>xfeE2D%FVQCO`5q2{auH4C_|u_luuj<8xdMrbB0}Q5$@4UhGO=Ra#puh;I}X>nDlmt_wcA%c'
    b'IzVk1XApASDmVj!bBfknGP~VEd8*t|pf7_RF!)lH92q72PP$g?W;5_S&T@69(uVV*EV>h?fy>A8WC$xA8Xx?o>z&7ito`CoiN+zZfN*Z^3gPg#h5@3`yiR@+'
    b'6RtHezj)C@W@$Ny4pqq1>UT}7-_m*fr2Kc3Yozcfay@4ogsw1!TK)}BP~PXp{LA=`I<Wln8vbAHzI;{wF?QiIJ=0&N=`u^I&H#*>w@KTcK#HBJXi-?)LiUHm'
    b'H{9Yq*Zne^k&FH3IE9}UJ8ABkW`DBNw%R$e3v7&Ravxpug4MAp+eK5h#+>+>jrbb{Z5UoIwnA`6zmLK6S^;gVf&slTXK7Ma!dV^_jl0UtzQqx?`!FbzFX$45'
    b'-UVs?IWDGA3CjU`AW&XXwJw5bD~Ir7P`|=WvzxjeH4WX%PUnMXKr>{kJ($bmsO+7y0g{X_BIZyE517InrMJ~nZc3~8&10t9%*nAO$*FuKEs*=um8=iFk;OVK'
    b'5XfN{?8QSnmvs!;#+^<wO>deuL;&bne8)}{By$RE96^E;1a?p1LG0~6jX`v>0ydkN(cQ5XhkUx0WYpn~HExvWfEHxdh%>D@iIZ&136ok-Z3JMK$Icf?fwZT@'
    b'2sqn7KTFE{m}C_3K?s>4C}yi2AMk*JIVJO0J;QTr4gv^@9Pw-g-4UV%GK~C8GIrOOsadhJO$=*G7&lhEte`lh57eBox`IF3BT>`~O|Bvul`Eopd=W2gh`Irq'
    b'nZYaxaJ1Jn&e)Pklyzka1Br?mntM@~wUOGO;TFv5`wB}upwS<LTjapbzD}m`>RBsLT6d=gtaBplGWO^>I0<F^6I(B0ZV^@Yp~&T{qvckm=2#~VuRH073HDo?'
    b'46O~!DwU97%v)cP*zT!PY<p}iqm*##tgF`b-Gj!;I?^3%XClCBiG(@=(waFMTb)r?@kp7j6(&juD!0O<I<3{W4o1b;MwSLXXiIb+t7jq-Gv80$X-?EVR%_}7'
    b'Wi33eV_!e^SY*`OA6wpjBAVt`()RVwuJu74|LoP%JTGngguH%vcwlJEpu?gDwkE#-La?^G)BZ=JZHVWiQYgqzN=@{oX+{tMB4gX1$^hJKrlP7B1sXhoe_F6M'
    b'TPu>)M#{!#$L6y|gqB+PG%VBHw*0nOFwCTl;Xr-#!e=y4AAD^@IG-FG>C_>3K!xQ45dRmXRMgPsQ2|Z<-V6RW3jTNz{Bmvn{2@H~kAMHiKZ5IjvrO8g{j#_Z'
    b'h&i%u2AnrAwQQL-ZRbmn-jV0lUI5ry6k=>5@h!z!Ok&nA#-q1`vwk@2Urolnv+%Ni-Wzf-`?wzt&M(gT=l$WtN|7Lz<<XdOB3Lb&%n8uZDd4FItQ7N9!){?u'
    b'PupgR+W*v2=UMeOoQ^H?DyxffVrE81Vi&xyylurUPR`%913sIBE!G;Uus@fv7BMnP<37!e(Njabr#a$#7CUaw+_BFY(Fu@Z4?~OBcSoEw0<74>u<QF~bOnP}'
    b'C2-ahar7~)8LVo(uN`avJ+lLPXdc>1i5*1FG8Sor)qRmK@9u*#fL*j?4}|JI&gxOt5-?!3U!>4{VSUyb*`fmyT6|I;5hb;Wziiv^z42i3{=AR-c-$Ml>u(f+'
    b'v<m>5e$Y=lzQ-5(X#wbRiGEs0I-KI4m?paYwD$nab!)H0nQ8%=^_{rtR@Hw;L_JSNSEuhW%%=ASCdX&v<zzfKot%9zDaEi83D5+&HcfA$=|?BcV2rVuDgs8O'
    b'dypjMrH<{Sa1VH)13Zw4GRtJf%#4%d8;~21e|h=KtDld5`H7k-R=lF6K2cjEH}rLVh^vC$LEgLkdr-sn7eCPn1jy&pk9fR;6nC3~=C%SB4-?&p^fb=Q6>k03'
    b'69zf^pWcT{*8aA2*XW$}`rh}=D^m_U4NuQTm#}Z&!hQ|k3@$H5mmIN4315{A%jPM|@m`)Q0&6;KG`^7M%`eoGhFubNhp}I(j7A`6l8s7>WcH;h2zxiBxK}Da'
    b'?@;^`Lv@3Aa)8P*C>O?nqIJrK^i9eHwt;<E+1?b|)0;*_2UBB^{;LoIxsduP;YAB29JNxyi(OMfn(m(pP`40HtwQs@ArTlx>|_S`&LCW}K(($)GP2n1n@eOS'
    b'EW>h8A}3P?MHZLkch>Q&SV#8o1gxV9(l{#Fll1xUkY^@Q9B<4pj(1E9>h3Qo_fHdSbDUCmA_rBd(eV?N*q*%8#h3IunLHCR;p=x=nr=Fo=4mSVBk34W{sxaG'
    b'9;;(YV4*vw@Q&}a@_cB8z5GmaJ<PYww*dPWNYE)&@?xiGrxyRG@8t1}$b%i+p9ht2O%`$u7r2CCD3an^(oLJi=Q|-OLQ;M#<#N8x$+Qc~(aH{<Ih;qSF4FA!'
    b'G}5uP><%)g+n-qwXUqBSxKCTmz+XpkcG0|lN|Hp#Hq|H)R9y!SWTFL+X1_;M7~!uc6dyffMLNr$z{a9%T}h^bmME>(cZuft97G~dJkc4{JaTCK?>h9eClm3)'
    b')I!8JBN!9IURWW;<?}G^f0uJ>bfec?RV;V{6-f#mnMi$;K_aViCmX?cqIr%)Q^wU(D@EePZrBZH2eVS;e5a9TM<eC(2LAi26Uld3rA``b1^adq3XlKXWZJ(7'
    b'Gbv+qCky8B{04N+`($B`e`S`C_+Pi89f}OP!l8$%xI+wqx-IfQVpEp-Nmvj$MN<_Kw6D~`wevdpxRX@JHYoYduAUFOqD&j#j$85Y-xcs@P9>DW@mtXd4&F*3'
    b'*WOe(WSOTTJBJ5S+_mAz-Sq0UBgiy7^JrmM9X2zOBlYn3Dz5-suB1XODLY#(U`wG6ex0a_yF1L$1xO`aHk`C;8D3f{Cp~T5qfU_83m|>dQbnCGuU(GkSr!=j'
    b'Gfi!~YCvB-k*5@6tYWwIMIJ{e+m(L3nQT>n^|h7$q8axpJ(x&#jz|tLI+wDW6}YeIHH%m#Kt52xaTMqe7*IJ8%j71N8ii=oQXkrYsHsxNp=Ra{xH{!ZUx%L9'
    b'XI0;^BMsAGSE8W9HS?AncIJpUTq9Qh@g-0ctJfqX)lcY7QX|P%JUN@*TcN2c7lH;yGJDk@OIAF8j*yo8PxQDMWv$=)(<r(r5o@vdo?_3fLB>{yl(my&Vrqk6'
    b'YS66IL6uzz4$4J5P2j-)BdV<SI$xG5gkf!O=ZBuZ^H>7ktz?V72=m$tm^={ORN!D<Q(vii(mmCMEo|`WdE^gnYss<YG+$_Ug1op%W<dFRZPCG{NKE{h(J0kY'
    b'y7?u5VcaF~<3Yt02PUo<9#KYAsv}rBVeWwnZZ}NX4uH1HBkK}DrKA+JvYzr2990Aq$>kSd6#KN4DSG1VJ=A3Qm=<!ZRnt<Z&e3>c5=PeY2T1ZmPtPJOcX0l%'
    b'*A_ved>AfLptSouMNg1M(RoV~q4XNembf@FY+;<WDvR7aM_j_?MU4`*v7AhyESD1bIEfvEO7P?fbQ+jz-(a=mEAEk{<$q7w2m_67Wqb?j&`@<w8x}77x#m3D'
    b'0r#G%>p;E9@Xnc~Ty^>Ex{1;0j25Z`z4b$WmuPLmhBI65+vXhB|5lTVE;g%t0!1U*Y>B0QEncOW@)jK^t;<QfM5z~)&1M78qUJ|6CA8=!s&dDyTBN-lZ^SOx'
    b'V4By)IH5R^I!x?*Jw73aLVCP%4!`k;HYY$c9byE1*CI*qr}c~^^srN+pg!BBgOj5d$1ht&gp;G=*Uh6}*(s#W%NM`A^2i5D>9?Tw$`A}-U5vnyEzPD?+}Grw'
    b'SJ9hB$F4xrnrP<<jNfK#IcsaiX#Jkf;!@0r96iU*$dm=Mx{opnqvBS40`sjrXgrDo^T(!)1NR`A4Qrcmg&qDWE$G+XX`GsJ!KO;vHRb_!iQV|t$vS2n$Y|I6'
    b'^l+Da5&ct_AjeVMtZBOhOebj6XAxQAw7sq4&|;5veNsI`2+gso#Ow{=?a;vY4sKlv*gtORBw7tBH`|s39*xqCpj5}|=IHFQo9u9xn|itKZZG$@;9Tog4$8nY'
    b'PhyQ-$hF!U=B_$40`N27q9XAGn57OcA8yxQ_)e49j=-zwa;rdF&*rx~@ccT_o<W@E0j*jsnJo9Qnl!zt*t1!1ze@Bx_R0!<ro}#Za&R#kPq4gBXbP2|^@i`R'
    b'dhhz`N>}Ahq$Fc+d#8QA(^VZRy~MKO)nrIzL+16Dtf?p#stvB&D-l$bj+$Dq#R!V8DXpV)N2uSRrx6gJTY7~yQlOMJCg)jPPK#tgf2Tm>Q>2Ij&<;dF#>Id-'
    b'(qs7*Adj+QW$&#U($WVK?CGAAv}2%gsbVz;@<~dM7eEnDmqn?wIn!aUv)U@f1I2dVJ+QN*DD%0BCP7U+^{#^r=_1K8`^f)n=|J|4wyxh`(g<G+hC@u?HavYl'
    b'8i%Sb5|{h(V#v<-!X&jU<1$eDGSH=N?R?&HY_}s3ogVRQ6pe>Bml}XcP4WY)c}uxGMRopbn|73Ec@-%4k2LN^b#n{@h9u|3bj1$PWgEW7qj%%pxfJxqYv{>n'
    b'd`WCWTT@!n(Hc|FJSrYEt_*YsPA8tkVv?h-dG)O_u}T8HtD#*B?4mcm?2p57|3B$w6`oMuy&m1FT1B<4E-okIKFrPSyZ<-fWtc6ncQpYT8%#db`j@=1=e>&y'
    b'OmKHK#6*5)zp*EUo{vh@s;xb)`AglV30CZ@TicaEGDSPDdEL08O51mQyWqT)oU+J{VurMgi%(<>!)$hO6#=`8+)Eq<?}j&nic8X1T2|-l!QEUkZrBUKVP9DZ'
    b'f_{*LR-vMa1$))})3UOPYiRX5Z)S0>`#?NY@`-0T_o;5NRAII@R?Wek`cg?sVU&tt70k;u&XD0MlaF&fEOyHzc3B=Lk<9~r?IA~8LOB<OUr2Z<&le4h>HxKU'
    b'dq|x_w;}ci61F8ASADJdMyX4J+g@3~OG*t2<Ao{`TWyRD3|rfojDgQZS)dK0H3(#r*7W%rymf52CR1@m$3qNJW5W^^`W&nGp#z1DJ=c{#jNnspRs#w3rNy<D'
    b'&G|;C$sDy)j>+PD%8Gm`g_1f4n%^@HtThptQPp9A)38dMXfJi=uMa?5yfWl(Pe~}HE`h<(tR{-vkj09&&qPI)N#94GlyOjjL370IUlZ}<QcR1OsH~~P{^&{e'
    b'1&`T8-A`Kgn5A<giMEFYMZci}ir2tXgfwFzBa7xY$=xzvmWt+>$G8R-*~o}-_<)Nlme|$rbi3-Tj%+f$DW#yMmGqQTQ1Bgu&WV96?yHeC?S$Z6{-pA`_FtqM'
    b'@p{%aJO4Da(_>1NTU+x`nZ2d(2yBK$uA-7bN}eLmV5SyL?~ROO<t!I31HQ~aKyV7RjHN<tv59<FwH6{(kX!9n;1hQ0a!D#X)Ae5!b4ef2f*s4aEMToJ$^)~7'
    b'-3HqlKBpDZ->*~kXGKY$uiHA?I<?yBXB;U@UTLBB;k3xh(sLW3P;P%~44)zZ!`4%nZXBC#QWub~t-@SNdgLO|CfU5V`rJ;+qB>pM<vaXXl2qvm1U^qOZ=r=D'
    b'QnS=faCQ%$rfzn2WaY3K)X_|It676IvDt?BkIlSJSGBT-R)x)GDWtBFOKr7QJoQYQG<r?4(rswzR22vp$Os;qe$h@j9nX}SRWutFQ+?$^y9z^fRiIgWh9D~e'
    b'n@Wo5GO0p~fi)e!4G*MAl&V?>G(nz&g)KBclop=a7t7MDpQpj+d)(i`zo}lSaivBsn1F;qjy*N{!^6dWR9f5_-`W(+Cz(C~Q~?P%YqF9~Z#c=9EWyCRi0c0='
    b'UI0Ne&sVX@wj}%2sbgZFTXrEC8nGVfpcsmXE@(!|XG`28A~6G9034zifV@`*aNcY8bP+-LxZwJ3$~9>Tj0q(u_+c4xY=D}Vjji=$iHdbndZpBglfHhg6;e<B'
    b'b*G#!oZgn2+U_*mp2pi#h_+D`mQ3z!qO0BbSk;cWaHAVVLef<HWeUq~F<g?2g$+vz3{`}&UQucrJo>QIXz4X0JT@DDXXpFDvi2I-3);l4(u_aY5<yKn&7Tn~'
    b'mThTgnDN`I{*2hsHa2sIurn;R*zcYpnl|9zE3J<k#De(IwsM3&Hv-$Ovpc|DSLgdi+jVPMx2DA5Vuf&Nukd;YV4dIlI9>bxwgYB-)#wQ*zEyDT=Pd-`JGXVr'
    b'*18jaoNa$^^JyXP6*F54B6WXrHh>|h3Y02BH2H9$N)fFBRIp-h+pe3H)h&`G>#Qw2v&*4~-rD}9_d|0RtVZqOx-<J~f-gb|zObulN@2m5N58!M@x{wSD?xOK'
    b'K8M;@mDMLwS=cqyDt%~|Eu@N+Rx|o7J-zzrrypM#Z(Z#la&q)a^!8g2i<gr5pNq&U%}Bf5l8kH@Og}g|esz5G@}+S`Wqv^5xb<w6Q!N`_00gIWZb>CIZKYbZ'
    b'CpS^2Ax@1hh-9j-<)<|?+r~te*99D3ynOxB&#%536PI2I$1qtdcB=iWttgg8n_9S-ry6Q!H@^0@F5S|poxRnX);gjSrD;GTYmdI1;CV^(wB+on+4kF_uk{`i'
    b'gBOl3hE394!*Yqn3_gI-{3t2(o5lmne8IKso4yCteNw;~RejENwR*Oqxs~k2Lfr_N^r6w$j8W)YrG^2LuDcxDoU#Jb8~4`Uc|`Rtb#-2f&~n~4t;vqlh=y*F'
    b'WDSnkxNNd+<yvnLYYC;*RRWoeNjT9F?oD0WdlOf#irLp!U=mm_Xei^tTzZLlM)MJS?>e=1owxxCzi(Rc?6SOUpd-f;WKL`_bl<B|(h}I>&2%9WmuYDGTZjz0'
    b'7APr@rY_7Ge_3!rP<pBYo#+QAJg&!|dZEYmI?}1L)HnOQiAjpw<dEz*gR`a&%`P^XR!8Y{fZ2WO=@1*}-OBC7TR?u<vg|$AF>NA3yZ&+>K*kH4lx=9CDyBK?'
    b'>t!Lgn&w0bZ1*C(izR0$B{vHd(n@_!(iwURd1?jI9Bfk7Rw|j$y;NT%2UNw|U~^~s9wEnTn#wL?WEry@>4HO(>^Ni0mslouXd30q3AwDK2xZ&xj0L;1-e4GB'
    b'zVC4$^PAB*{Z^F~)thUMPR9F8oSKA_Hu*fQLCCjS>df}8f}SGgwnyWyI4NLy59LHA7ZwHy<Rd266Pzf8aBZT3YG!Zk@<8p%Zp*nAJR04YD%Wf9Aw$9DGZiPT'
    b'l|>2JQoc*|;93#Ooep$$oE6NfUd_fDRviNETf7x`m5^owaDn*N1QjEJae!?Aqe!Fe@JXMp2_gqHZI3?|x3>b5t=VhB$=R2;httC*%+syF*Etfr;B#RVmNNuu'
    b'5Hggo5~KTwczQc+wwM_n3Ho?xg}>3Pz8F%9vUNV}s-VNn%$3wP16f7FJqgJA!dIXB+W)V80^J|gcP%QBE6#RHmEhT#NJMvv<u-E!?jN!$>q;y2XMX8O99KHf'
    b'v0nd8%vgDlyVsh67qXd^P?>#*Y{^JfOk}B7oNdT;pr&cmP-_IH4Y8`TNx*5a2GO@QZyrL%Np8KJ;LT4#3LRhPmKA7T0Xb6NqI+JP&6I%1whE)Y6>&0;?&78&'
    b'2@7U~uw<sBKJ}AdDuGX4I`SWn!@{H<jTvooET{HVeyc)uN%GZRH40SjA91Qf#kUdTY~1mUehb!=rA`a5MznH7T8cOZJs^1T0uP86NBpq~y>`t*cF1-8O^Z}T'
    b'^x7px$I0D&Wjpq?4F0-x@Yh}$sX1^no+m1&Nzyqg*~-?QG>bmXk(J5_(ikp3Pz7#rxlivJUfB*?Ab8Ox)igmUqR%?vu3_V=(f(um{I!*_A(b?T$J)|NWAxXN'
    b'>)=JFq_Y*<D3A@58!U;IEIforAh7CQ#EY0jqW!@2x?OzO1}<|r><2g&2HGH_h@cMW`0U#cWcFdaCgzaN9r%!o%0T6g!SkPsl+w?aD@)(q^oOUTH+ZEr9GwsF'
    b'stGSi@J8oyGQK*UjK<;UqCdvqo=_zx#EU+4(>Cd!U!39XUT^4&`Wp?;J{)}gKX8I5qW'
)

class PortablePredicateLanguageCoreVerificationCode(str, Enum):
    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    CANONICAL_MISMATCH = "CANONICAL_MISMATCH"
    PIN_MISMATCH = "PIN_MISMATCH"
    CONTRACT_DRIFT = "CONTRACT_DRIFT"
    RESULT_INVALID = "RESULT_INVALID"


_ERROR_MESSAGES: Final = {
    PortablePredicateLanguageCoreVerificationCode.INPUT_TYPE: (
        "portable predicate-language verifier input has an invalid exact type"
    ),
    PortablePredicateLanguageCoreVerificationCode.INPUT_RESOURCE: (
        "portable predicate-language verifier input exceeds its resource ceiling"
    ),
    PortablePredicateLanguageCoreVerificationCode.JSON_INVALID: (
        "portable predicate-language verifier JSON is invalid"
    ),
    PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID: (
        "portable predicate-language verifier schema is invalid"
    ),
    PortablePredicateLanguageCoreVerificationCode.CANONICAL_MISMATCH: (
        "portable predicate-language verifier bytes are not canonical"
    ),
    PortablePredicateLanguageCoreVerificationCode.PIN_MISMATCH: (
        "portable predicate-language verifier pin does not match"
    ),
    PortablePredicateLanguageCoreVerificationCode.CONTRACT_DRIFT: (
        "portable predicate-language verifier frozen snapshot drifted"
    ),
    PortablePredicateLanguageCoreVerificationCode.RESULT_INVALID: (
        "portable predicate-language verification result is invalid"
    ),
}


class PortablePredicateLanguageCoreVerificationError(ValueError):
    def __init__(self, code: PortablePredicateLanguageCoreVerificationCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


class _DuplicateKeyError(ValueError):
    pass


@dataclass(frozen=True)
class PortablePredicateLanguageCoreVerificationPinsV1:
    semantic_core_contract_sha256: str


@dataclass(frozen=True)
class PortablePredicateLanguageCoreVerificationResultV1:
    artifact_type: str
    canonical_contract_verified: bool
    contract_byte_count: int
    contract_plain_sha256: str
    contract_sha256: str
    empirical_result_established: bool
    evaluator_executed: bool
    frozen_snapshot_identity_verified: bool
    profile_interface_sha256: str
    profile_interface_verified: bool
    runtime_program_validated: bool
    verifier_id: str
    verification_status_id: str


def _fail(code: PortablePredicateLanguageCoreVerificationCode) -> None:
    raise PortablePredicateLanguageCoreVerificationError(code)


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    if len(encoded) > _MAX_ARTIFACT_BYTES:
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_RESOURCE)
    return encoded


def _object_without_duplicates(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError


def _reject_float(_: str) -> None:
    raise ValueError


def _bounded_integer(value: str) -> int:
    if len(value.lstrip("-")) > 20:
        raise ValueError
    return int(value)


def _same_exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(
            _same_exact(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            _same_exact(a, b) for a, b in zip(left, right)
        )
    return left == right


def _json_string_byte_count(value: str, maximum: int) -> int:
    if maximum < 0:
        return 0
    if maximum < 2:
        return maximum + 1
    if len(value) > maximum - 2:
        return maximum + 1
    count = 2
    for character in value:
        codepoint = ord(character)
        if character in '"\\\b\f\n\r\t':
            count += 2
        elif codepoint < 0x20:
            count += 6
        elif codepoint <= 0x7E:
            count += 1
        elif codepoint <= 0xFFFF:
            count += 6
        else:
            count += 12
        if count > maximum:
            return count
    return count


def _bounded_exact_json_status(value: object) -> str:
    item_count = 0
    encoded_byte_count = 0
    active_container_ids = set()
    frames = []
    current = value
    depth = 1
    while True:
        item_count += 1
        if item_count > _MAX_JSON_ITEMS or depth > _MAX_JSON_DEPTH:
            return "resource-invalid"

        current_type = type(current)
        if current_type is str:
            encoded_byte_count += _json_string_byte_count(
                current, _MAX_ARTIFACT_BYTES - encoded_byte_count
            )
        elif current_type is bool:
            encoded_byte_count += 4 if current else 5
        elif current_type is int:
            if abs(current) >= 10**20:
                return "schema-invalid"
            encoded_byte_count += len(str(current))
        elif current_type in (list, dict):
            container_id = id(current)
            if container_id in active_container_ids:
                return "schema-invalid"
            if len(current) > _MAX_JSON_ITEMS - item_count:
                return "resource-invalid"

            element_count = len(current)
            encoded_byte_count += (
                2
                + max(element_count - 1, 0)
                + (element_count if current_type is dict else 0)
            )
            if current_type is dict:
                if any(type(key) is not str for key in current):
                    return "schema-invalid"
                for key in current:
                    encoded_byte_count += _json_string_byte_count(
                        key, _MAX_ARTIFACT_BYTES - encoded_byte_count
                    )
                    if encoded_byte_count > _MAX_ARTIFACT_BYTES:
                        return "resource-invalid"
                children = iter(current.values())
            else:
                children = iter(current)
            active_container_ids.add(container_id)
            frames.append((children, depth + 1, container_id))
        else:
            return "schema-invalid"

        if encoded_byte_count > _MAX_ARTIFACT_BYTES:
            return "resource-invalid"

        while frames:
            children, child_depth, container_id = frames[-1]
            try:
                current = next(children)
            except StopIteration:
                frames.pop()
                active_container_ids.remove(container_id)
                continue
            except RuntimeError:
                return "schema-invalid"
            depth = child_depth
            break
        else:
            return "valid"


def _strict_json(value: bytes) -> object:
    try:
        return json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
            parse_int=_bounded_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
        _DuplicateKeyError,
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.JSON_INVALID)


def _frozen_contract_bytes() -> bytes:
    try:
        raw = zlib.decompress(base64.b85decode(_COMPRESSED_CONTRACT_B85))
    except (ValueError, zlib.error):
        _fail(PortablePredicateLanguageCoreVerificationCode.CONTRACT_DRIFT)
    if (
        len(raw) != _V1_BYTE_COUNT
        or hashlib.sha256(raw).hexdigest() != _V1_PLAIN_SHA256
        or _domain_sha256(_CONTRACT_ARTIFACT_TYPE, raw) != _V1_SHA256
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.CONTRACT_DRIFT)
    return raw


def portable_predicate_language_core_verifier_contract_tree() -> dict:
    value = _strict_json(_frozen_contract_bytes())
    if type(value) is not dict:
        _fail(PortablePredicateLanguageCoreVerificationCode.CONTRACT_DRIFT)
    return value


def portable_predicate_language_core_verifier_contract_bytes() -> bytes:
    return _frozen_contract_bytes()


def portable_predicate_language_core_verifier_contract_plain_sha256() -> str:
    return hashlib.sha256(_frozen_contract_bytes()).hexdigest()


def portable_predicate_language_core_verifier_contract_sha256() -> str:
    return _domain_sha256(_CONTRACT_ARTIFACT_TYPE, _frozen_contract_bytes())


def parse_portable_predicate_language_core_verifier_contract(
    value: bytes,
) -> dict:
    """Strictly parse the exact verifier-lane frozen core snapshot."""

    if type(value) is not bytes:
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_TYPE)
    if not value or len(value) > _MAX_ARTIFACT_BYTES:
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_RESOURCE)
    decoded = _strict_json(value)
    json_status = _bounded_exact_json_status(decoded)
    if json_status == "schema-invalid":
        _fail(
            PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
        )
    if json_status != "valid":
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_RESOURCE)
    expected = portable_predicate_language_core_verifier_contract_tree()
    if not _same_exact(decoded, expected):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    if value != _frozen_contract_bytes():
        _fail(
            PortablePredicateLanguageCoreVerificationCode.CANONICAL_MISMATCH
        )
    return expected


def portable_predicate_language_core_verifier_profile_interface_tree() -> dict:
    tree = portable_predicate_language_core_verifier_contract_tree()
    interface = tree.get("profile_interface")
    if type(interface) is not dict:
        _fail(PortablePredicateLanguageCoreVerificationCode.CONTRACT_DRIFT)
    return interface


def portable_predicate_language_core_verifier_profile_interface_sha256() -> str:
    return _domain_sha256(
        _PROFILE_INTERFACE_ARTIFACT_TYPE,
        _canonical_json(
            portable_predicate_language_core_verifier_profile_interface_tree()
        ),
    )


def _is_identifier(value: object) -> bool:
    return (
        type(value) is str
        and value.isascii()
        and 1 <= len(value.encode("ascii")) <= 512
        and _IDENTIFIER_RE.fullmatch(value) is not None
    )


def _is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _exact_keys(value: object, keys: tuple) -> bool:
    return type(value) is dict and set(value) == set(keys)


def _unique_ids(value: object, *, nonempty: bool = True) -> bool:
    return (
        type(value) is list
        and (bool(value) or not nonempty)
        and all(_is_identifier(item) for item in value)
        and len(value) == len(set(value))
    )


def _rows_have_unique_id(rows: list, field: str) -> bool:
    values = [row[field] for row in rows]
    return len(values) == len(set(values))


def _validate_portable_predicate_profile_verifier_tree_impl(
    profile_tree: object,
) -> dict:
    if type(profile_tree) is not dict:
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    json_status = _bounded_exact_json_status(profile_tree)
    if json_status == "schema-invalid":
        _fail(
            PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
        )
    if json_status != "valid":
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_RESOURCE)
    _canonical_json(profile_tree)

    interface = (
        portable_predicate_language_core_verifier_profile_interface_tree()
    )
    maxima = interface["maximum_profile_registry_counts"]
    fields = tuple(interface["closed_profile_exact_field_ids"])
    if not _exact_keys(profile_tree, fields):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    tree = profile_tree
    identifiers = (
        "artifact_type",
        "digest_computation_id",
        "encoding_id",
        "format_version",
        "implementation_status_id",
        "profile_class_id",
        "profile_id",
        "profile_interface_id",
        "profile_verification_result_artifact_type",
        "validation_scope_id",
    )
    if (
        any(not _is_identifier(tree[field]) for field in identifiers)
        or tree["format_version"] != "1"
        or tree["encoding_id"] != _ENCODING_ID
        or tree["digest_computation_id"] != _DIGEST_COMPUTATION_ID
        or not _is_sha256(tree["core_contract_sha256"])
        or tree["core_contract_sha256"] != _V1_SHA256
        or not _is_sha256(tree["core_profile_interface_sha256"])
        or tree["core_profile_interface_sha256"] != _V1_INTERFACE_SHA256
        or tree["profile_interface_id"] != interface["profile_interface_id"]
        or not _unique_ids(
            tree["authority_class_ids"], nonempty=False
        )
        or len(tree["authority_class_ids"])
        > maxima["authority_class_ids"]
        or not _unique_ids(tree["public_error_ids"])
        or len(tree["public_error_ids"]) > maxima["public_error_ids"]
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    anchors = tree["anchor_contract_rows"]
    if (
        type(anchors) is not list
        or len(anchors) > maxima["anchor_contract_rows"]
        or any(
            not _exact_keys(
                row,
                ("anchor_role_id", "artifact_type_id", "contract_sha256"),
            )
            or not _is_identifier(row["anchor_role_id"])
            or not _is_identifier(row["artifact_type_id"])
            or not _is_sha256(row["contract_sha256"])
            for row in anchors
        )
        or not _rows_have_unique_id(anchors, "anchor_role_id")
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    domains = tree["artifact_domain_rows"]
    if (
        type(domains) is not list
        or not domains
        or len(domains) > maxima["artifact_domain_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "artifact_role_id",
                    "artifact_type_id",
                    "digest_domain_id",
                    "identity_semantics_id",
                ),
            )
            or not _is_identifier(row["artifact_role_id"])
            or not _is_identifier(row["artifact_type_id"])
            or not _is_identifier(row["digest_domain_id"])
            or row["digest_domain_id"] != row["artifact_type_id"]
            or row["identity_semantics_id"] != "DOMAIN_SEPARATED_SHA256"
            for row in domains
        )
        or not _rows_have_unique_id(domains, "artifact_role_id")
        or not _rows_have_unique_id(domains, "artifact_type_id")
        or [
            row["artifact_role_id"]
            for row in domains[
                : len(_REQUIRED_RUNTIME_ARTIFACT_ROLE_IDS)
            ]
        ]
        != list(_REQUIRED_RUNTIME_ARTIFACT_ROLE_IDS)
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    anchor_role_ids = {row["anchor_role_id"] for row in anchors}
    artifact_role_ids = {row["artifact_role_id"] for row in domains}
    reserved_artifact_types = [
        tree["artifact_type"],
        tree["profile_verification_result_artifact_type"],
        *interface["reserved_core_metadata_artifact_type_ids"],
        *[row["artifact_type_id"] for row in anchors],
        *[row["artifact_type_id"] for row in domains],
    ]
    if (
        anchor_role_ids.intersection(artifact_role_ids)
        or anchor_role_ids.intersection(
            _RESERVED_METADATA_ARTIFACT_ROLE_IDS
        )
        or artifact_role_ids.intersection(
            _RESERVED_METADATA_ARTIFACT_ROLE_IDS
        )
        or len(reserved_artifact_types) != len(set(reserved_artifact_types))
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    error_rows = tree["public_error_role_rows"]
    roles = list(_REQUIRED_PUBLIC_ERROR_ROLE_IDS)
    if (
        type(error_rows) is not list
        or any(type(row) is not dict for row in error_rows)
        or [row.get("public_error_role_id") for row in error_rows] != roles
        or any(
            not _exact_keys(
                row, ("public_error_role_id", "public_error_id")
            )
            or not _is_identifier(row["public_error_role_id"])
            or row["public_error_id"] not in tree["public_error_ids"]
            for row in error_rows
        )
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    parameters = tree["profile_parameter_rows"]
    slots = list(_REQUIRED_PROFILE_PARAMETER_SLOT_IDS)
    if (
        type(parameters) is not list
        or len(parameters) < len(slots)
        or len(parameters) > maxima["profile_parameter_rows"]
        or any(type(row) is not dict for row in parameters)
        or [
            row.get("parameter_slot_id")
            for row in parameters[: len(slots)]
        ]
        != slots
        or any(
            not _exact_keys(
                row, ("parameter_slot_id", "parameter_value_id")
            )
            or not _is_identifier(row["parameter_slot_id"])
            or not _is_identifier(row["parameter_value_id"])
            for row in parameters
        )
        or not _rows_have_unique_id(parameters, "parameter_slot_id")
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    declared_slots = {row["parameter_slot_id"] for row in parameters}

    locators = tree["locator_extension_rows"]
    if (
        type(locators) is not list
        or len(locators) > maxima["locator_extension_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "exact_configuration_field_ids",
                    "exact_empty_placeholder_field_ids",
                    "locator_kind_id",
                    "locator_primitive_id",
                    "validation_primitive_id",
                    "validation_rule_id",
                ),
            )
            or not _is_identifier(row["locator_kind_id"])
            or row["locator_primitive_id"]
            not in _LOCATOR_PRIMITIVE_IDS
            or not _unique_ids(
                row["exact_configuration_field_ids"], nonempty=False
            )
            or not _unique_ids(
                row["exact_empty_placeholder_field_ids"],
                nonempty=False,
            )
            or not set(
                row["exact_empty_placeholder_field_ids"]
            ).issubset(row["exact_configuration_field_ids"])
            or row["validation_primitive_id"]
            != interface["profile_locator_validation_primitive_id"]
            or not _is_identifier(row["validation_rule_id"])
            for row in locators
        )
        or not _rows_have_unique_id(locators, "locator_kind_id")
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    purposes = tree["program_purpose_rows"]
    relation_primitive_ids = set(_PURPOSE_RELATION_PRIMITIVE_IDS)
    if (
        type(purposes) is not list
        or not purposes
        or any(type(row) is not dict for row in purposes)
        or len(purposes) > maxima["program_purpose_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "exact_binding_field_ids",
                    "program_purpose_id",
                    "purpose_relation_rows",
                    "validation_primitive_id",
                    "validation_rule_id",
                ),
            )
            or not _unique_ids(
                row["exact_binding_field_ids"], nonempty=False
            )
            or not _is_identifier(row["program_purpose_id"])
            or type(row["purpose_relation_rows"]) is not list
            or not _is_identifier(row["validation_rule_id"])
            for row in purposes
        )
        or len([row["program_purpose_id"] for row in purposes])
        != len(set(row["program_purpose_id"] for row in purposes))
        or purposes[0]["program_purpose_id"]
        != next(
            row["parameter_value_id"]
            for row in parameters
            if row["parameter_slot_id"] == "primary-program-purpose-id"
        )
        or any(
            row["validation_primitive_id"]
            != interface[
                "profile_program_purpose_validation_primitive_id"
            ]
            for row in purposes
        )
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    purpose_relation_rows = [
        relation
        for purpose in purposes
        for relation in purpose["purpose_relation_rows"]
    ]
    purpose_equality_rows = [
        equality
        for relation in purpose_relation_rows
        if type(relation) is dict
        and relation.get("relation_primitive_id")
        == "exactly-one-pinned-anchor-row-canonical-equality-v1"
        for equality in (
            relation.get("ordered_equality_rows", [])
            if type(relation.get("ordered_equality_rows")) is list
            else []
        )
    ]
    if (
        len(purpose_relation_rows)
        > maxima["program_purpose_relation_rows"]
        or len(purpose_equality_rows)
        > maxima["program_purpose_equality_rows"]
        or any(type(row) is not dict for row in purpose_relation_rows)
        or any(
            not _is_identifier(row.get("relation_primitive_id"))
            or row.get("relation_primitive_id")
            not in relation_primitive_ids
            for row in purpose_relation_rows
        )
        or any(
            not _is_identifier(row.get("relation_id"))
            for row in purpose_relation_rows
        )
        or len(
            [row.get("relation_id") for row in purpose_relation_rows]
        )
        != len(
            set(row.get("relation_id") for row in purpose_relation_rows)
        )
        or any(
            [
                row.get("relation_id")
                for row in purpose["purpose_relation_rows"]
            ]
            != sorted(
                row.get("relation_id")
                for row in purpose["purpose_relation_rows"]
            )
            for purpose in purposes
        )
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    for purpose in purposes:
        binding_field_ids = purpose["exact_binding_field_ids"]
        binding_field_index = {
            field_id: index
            for index, field_id in enumerate(binding_field_ids)
        }
        for relation in purpose["purpose_relation_rows"]:
            primitive_id = relation["relation_primitive_id"]
            if primitive_id == (
                "exactly-one-pinned-anchor-row-canonical-equality-v1"
            ):
                if not _exact_keys(
                    relation,
                    (
                        "anchor_role_id",
                        "anchor_row_array_path_ids",
                        "ordered_equality_rows",
                        "relation_id",
                        "relation_primitive_id",
                    ),
                ):
                    _fail(
                        PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
                    )
                path_ids = relation["anchor_row_array_path_ids"]
                equality_rows = relation["ordered_equality_rows"]
                if (
                    not _is_identifier(relation["anchor_role_id"])
                    or relation["anchor_role_id"] not in anchor_role_ids
                    or not _is_identifier(relation["relation_id"])
                    or type(path_ids) is not list
                    or not 1 <= len(path_ids) <= 16
                    or any(not _is_identifier(item) for item in path_ids)
                    or type(equality_rows) is not list
                    or not 1 <= len(equality_rows) <= 64
                    or any(
                        not _exact_keys(
                            equality,
                            (
                                "anchor_row_value_path_ids",
                                "purpose_binding_field_id",
                            ),
                        )
                        or type(equality["anchor_row_value_path_ids"])
                        is not list
                        or not 1
                        <= len(equality["anchor_row_value_path_ids"])
                        <= 16
                        or any(
                            not _is_identifier(item)
                            for item in equality[
                                "anchor_row_value_path_ids"
                            ]
                        )
                        or not _is_identifier(
                            equality["purpose_binding_field_id"]
                        )
                        or equality["purpose_binding_field_id"]
                        not in binding_field_index
                        for equality in equality_rows
                    )
                    or len(
                        [
                            equality["purpose_binding_field_id"]
                            for equality in equality_rows
                        ]
                    )
                    != len(
                        {
                            equality["purpose_binding_field_id"]
                            for equality in equality_rows
                        }
                    )
                    or len(
                        [
                            tuple(equality["anchor_row_value_path_ids"])
                            for equality in equality_rows
                        ]
                    )
                    != len(
                        {
                            tuple(equality["anchor_row_value_path_ids"])
                            for equality in equality_rows
                        }
                    )
                    or [
                        binding_field_index[
                            equality["purpose_binding_field_id"]
                        ]
                        for equality in equality_rows
                    ]
                    != sorted(
                        binding_field_index[
                            equality["purpose_binding_field_id"]
                        ]
                        for equality in equality_rows
                    )
                ):
                    _fail(
                        PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
                    )
            elif primitive_id == (
                "purpose-identifiers-exactly-covered-by-input-locators-v1"
            ):
                if (
                    not _exact_keys(
                        relation,
                        (
                            "locator_value_field_id",
                            "purpose_binding_field_id",
                            "relation_id",
                            "relation_primitive_id",
                        ),
                    )
                    or not _is_identifier(relation["relation_id"])
                    or not _is_identifier(
                        relation["locator_value_field_id"]
                    )
                    or not _is_identifier(
                        relation["purpose_binding_field_id"]
                    )
                    or relation["purpose_binding_field_id"]
                    not in binding_field_index
                ):
                    _fail(
                        PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
                    )
            else:
                _fail(
                    PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
                )

    profile_field_rows = tree["profile_field_schema_rows"]
    semantic_role_by_id = {
        row["semantic_role_id"]: row
        for row in interface["profile_field_semantic_role_rows"]
    }
    core_value_schema_by_field = {
        field_id: row["value_schema_id"]
        for row in portable_predicate_language_core_verifier_contract_tree()[
            "field_value_schema_rows"
        ]
        for field_id in row["field_ids"]
    }
    locator_field_sets = [
        set(row["exact_configuration_field_ids"]) for row in locators
    ]
    purpose_field_sets = [
        set(row["exact_binding_field_ids"]) for row in purposes
    ]
    locator_field_ids = (
        set().union(*locator_field_sets) if locators else set()
    )
    purpose_field_ids = set().union(*purpose_field_sets)
    referenced_profile_field_ids = locator_field_ids | purpose_field_ids
    if (
        type(profile_field_rows) is not list
        or len(profile_field_rows) > maxima["profile_field_schema_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "field_id",
                    "role_parameter_id",
                    "semantic_role_id",
                    "value_schema_id",
                ),
            )
            or not _is_identifier(row["field_id"])
            or not _is_identifier(row["role_parameter_id"])
            or not _is_identifier(row["semantic_role_id"])
            or row["semantic_role_id"] not in semantic_role_by_id
            or row["value_schema_id"]
            not in _PROFILE_FIELD_VALUE_SCHEMA_IDS
            or row["value_schema_id"]
            not in semantic_role_by_id[row["semantic_role_id"]][
                "admitted_value_schema_ids"
            ]
            for row in profile_field_rows
        )
        or not _rows_have_unique_id(profile_field_rows, "field_id")
        or [row["field_id"] for row in profile_field_rows]
        != sorted(row["field_id"] for row in profile_field_rows)
        or {row["field_id"] for row in profile_field_rows}
        != referenced_profile_field_ids
        or any(
            row["field_id"] in core_value_schema_by_field
            and row["value_schema_id"]
            != core_value_schema_by_field[row["field_id"]]
            for row in profile_field_rows
        )
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    profile_field_by_id = {
        row["field_id"]: row for row in profile_field_rows
    }

    no_parameter_role_ids = {
        "opaque-identifier",
        "ordered-unique-identifiers",
        "locator-kind-self",
        "path-segments",
        "nonnegative-count",
        "typed-key-components",
        "prior-input-resolved-operand",
    }
    artifact_parameter_role_ids = {
        "artifact-type-for-role",
        "artifact-identity-semantics-for-role",
        "artifact-identity-sha256-for-role",
    }
    anchor_parameter_role_ids = {
        "anchor-artifact-type-for-role",
        "anchor-contract-sha256-for-role",
    }

    def fields_share_one_group(
        field_id: str,
        other_field_id: str,
        groups: list,
    ) -> bool:
        return any(
            {field_id, other_field_id}.issubset(group) for group in groups
        )

    for row in profile_field_rows:
        field_id = row["field_id"]
        parameter_id = row["role_parameter_id"]
        role_id = row["semantic_role_id"]
        if role_id in no_parameter_role_ids:
            valid_parameter = parameter_id == "NONE"
        elif role_id in artifact_parameter_role_ids:
            valid_parameter = parameter_id in artifact_role_ids
        elif role_id in anchor_parameter_role_ids:
            valid_parameter = parameter_id in anchor_role_ids
        elif role_id == "identifier-member-of-purpose-field":
            target = profile_field_by_id.get(parameter_id)
            valid_parameter = (
                field_id in locator_field_ids
                and parameter_id != field_id
                and parameter_id in purpose_field_ids
                and target is not None
                and target["value_schema_id"]
                == "ordered-identifier-array-v1"
                and all(
                    parameter_id in purpose_field_set
                    for purpose_field_set in purpose_field_sets
                )
            )
        elif role_id == "index-below-field":
            target = profile_field_by_id.get(parameter_id)
            valid_parameter = (
                parameter_id != field_id
                and target is not None
                and target["value_schema_id"]
                == "nonnegative-index-or-count-integer-v1"
                and target["semantic_role_id"] == "nonnegative-count"
                and fields_share_one_group(
                    field_id,
                    parameter_id,
                    locator_field_sets + purpose_field_sets,
                )
            )
        else:
            valid_parameter = False
        placement_is_valid = (
            role_id
            not in {
                "locator-kind-self",
                "path-segments",
                "typed-key-components",
                "prior-input-resolved-operand",
                "identifier-member-of-purpose-field",
            }
            or field_id in locator_field_ids
        )
        if not valid_parameter or not placement_is_valid:
            _fail(
                PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
            )

    selection_role_ids = {
        "path-segments",
        "nonnegative-count",
        "index-below-field",
        "typed-key-components",
        "prior-input-resolved-operand",
    }
    locator_constraint_by_primitive = {
        row["locator_primitive_id"]: row
        for row in interface[
            "locator_primitive_profile_field_constraint_rows"
        ]
    }
    for locator in locators:
        configuration_field_ids = locator["exact_configuration_field_ids"]
        placeholder_field_ids = locator[
            "exact_empty_placeholder_field_ids"
        ]
        placeholder_field_id_set = set(placeholder_field_ids)
        locator_field_rows = [
            profile_field_by_id[field_id]
            for field_id in configuration_field_ids
        ]
        effective_locator_field_rows = [
            row
            for row in locator_field_rows
            if row["field_id"] not in placeholder_field_id_set
        ]
        locator_role_ids = [
            row["semantic_role_id"] for row in effective_locator_field_rows
        ]
        primitive_id = locator["locator_primitive_id"]
        constraint = locator_constraint_by_primitive[primitive_id]
        admitted_selection_role_ids = set(
            constraint["admitted_selection_semantic_role_ids"]
        )
        required_role_counts = {
            row["semantic_role_id"]: row["required_count"]
            for row in constraint["required_semantic_role_count_rows"]
        }
        path_field_ids = [
            row["field_id"]
            for row in locator_field_rows
            if row["semantic_role_id"] == "path-segments"
        ]
        if (
            placeholder_field_ids
            != [
                field_id
                for field_id in configuration_field_ids
                if field_id in placeholder_field_id_set
            ]
            or len(placeholder_field_ids) > 1
            or any(
                profile_field_by_id[field_id]["semantic_role_id"]
                != "path-segments"
                or profile_field_by_id[field_id]["value_schema_id"]
                != "ordered-exact-object-row-array-v1"
                for field_id in placeholder_field_ids
            )
            or (
                primitive_id == "direct-bound-value"
                and placeholder_field_ids != path_field_ids
            )
            or (
                primitive_id != "direct-bound-value"
                and bool(placeholder_field_ids)
            )
            or set(locator_role_ids).intersection(selection_role_ids)
            - admitted_selection_role_ids
            or any(
                locator_role_ids.count(role_id) != required_count
                for role_id, required_count in required_role_counts.items()
            )
            or any(
                locator_role_ids.count(role_id) > 1
                for role_id in admitted_selection_role_ids
            )
            or any(
                row["role_parameter_id"]
                not in {
                    candidate["field_id"]
                    for candidate in effective_locator_field_rows
                    if candidate["semantic_role_id"]
                    == "nonnegative-count"
                }
                for row in effective_locator_field_rows
                if row["semantic_role_id"] == "index-below-field"
            )
        ):
            _fail(
                PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
            )

    purpose_member_field_rows = [
        row
        for row in profile_field_rows
        if row["semantic_role_id"] == "identifier-member-of-purpose-field"
    ]
    for purpose in purposes:
        coverage_relations = [
            relation
            for relation in purpose["purpose_relation_rows"]
            if relation["relation_primitive_id"]
            == "purpose-identifiers-exactly-covered-by-input-locators-v1"
        ]
        for relation in coverage_relations:
            locator_field = profile_field_by_id.get(
                relation["locator_value_field_id"]
            )
            purpose_field = profile_field_by_id.get(
                relation["purpose_binding_field_id"]
            )
            if (
                locator_field is None
                or purpose_field is None
                or relation["locator_value_field_id"]
                not in locator_field_ids
                or locator_field["semantic_role_id"]
                != "identifier-member-of-purpose-field"
                or locator_field["value_schema_id"]
                != "strict-identifier-string-v1"
                or locator_field["role_parameter_id"]
                != relation["purpose_binding_field_id"]
                or purpose_field["semantic_role_id"]
                != "ordered-unique-identifiers"
                or purpose_field["value_schema_id"]
                != "ordered-identifier-array-v1"
            ):
                _fail(
                    PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
                )
        for member_field in purpose_member_field_rows:
            if sum(
                relation["locator_value_field_id"]
                == member_field["field_id"]
                and relation["purpose_binding_field_id"]
                == member_field["role_parameter_id"]
                for relation in coverage_relations
            ) != 1:
                _fail(
                    PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
                )

    locator_rows_by_field_shape = {}
    for locator in locators:
        shape = frozenset(locator["exact_configuration_field_ids"])
        locator_rows_by_field_shape.setdefault(shape, []).append(locator)
    for shape, shape_locators in locator_rows_by_field_shape.items():
        if len(shape_locators) > 1 and sum(
            profile_field_by_id[field_id]["semantic_role_id"]
            == "locator-kind-self"
            for field_id in shape
        ) != 1:
            _fail(
                PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
            )

    specializations = tree["operator_specialization_rows"]
    primitive_by_id = {
        row["primitive_id"]: row
        for row in interface["profile_bound_operator_primitive_rows"]
    }
    core_operator_ids = {
        row["operator_id"]
        for row in portable_predicate_language_core_verifier_contract_tree()[
            "operator_contract"
        ]["operator_rows"]
    }
    if (
        type(specializations) is not list
        or len(specializations) > maxima["operator_specialization_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "exposed_operator_id",
                    "operand_source_rule_id",
                    "ordered_parameter_slot_ids",
                    "primitive_id",
                    "type_and_truth_rule_id",
                ),
            )
            or not _is_identifier(row["primitive_id"])
            or row["primitive_id"] not in primitive_by_id
            or not _is_identifier(row["exposed_operator_id"])
            or row["exposed_operator_id"] in core_operator_ids
            or not _unique_ids(
                row["ordered_parameter_slot_ids"], nonempty=False
            )
            or not set(row["ordered_parameter_slot_ids"]).issubset(
                declared_slots
            )
            or set(row["ordered_parameter_slot_ids"]).intersection(slots)
            or len(row["ordered_parameter_slot_ids"])
            < primitive_by_id[row["primitive_id"]][
                "minimum_parameter_slot_count"
            ]
            or len(row["ordered_parameter_slot_ids"])
            > primitive_by_id[row["primitive_id"]][
                "maximum_parameter_slot_count"
            ]
            or row["operand_source_rule_id"]
            != primitive_by_id[row["primitive_id"]][
                "operand_source_rule_id"
            ]
            or row["type_and_truth_rule_id"]
            != primitive_by_id[row["primitive_id"]][
                "type_and_truth_rule_id"
            ]
            for row in specializations
        )
        or not _rows_have_unique_id(
            specializations, "exposed_operator_id"
        )
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    refinements = tree["interval_refinement_rows"]
    refinement_primitive_ids = {
        row["refinement_primitive_id"]
        for row in interface["interval_refinement_primitive_rows"]
    }
    if (
        type(refinements) is not list
        or len(refinements) > maxima["interval_refinement_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "endpoint_parameter_slot_id",
                    "exposed_refinement_id",
                    "refinement_primitive_id",
                    "validation_rule_id",
                ),
            )
            or not _is_identifier(row["refinement_primitive_id"])
            or row["refinement_primitive_id"]
            not in refinement_primitive_ids
            or not _is_identifier(row["endpoint_parameter_slot_id"])
            or row["endpoint_parameter_slot_id"] not in declared_slots
            or row["endpoint_parameter_slot_id"] in slots
            or not _is_identifier(row["exposed_refinement_id"])
            or not _is_identifier(row["validation_rule_id"])
            for row in refinements
        )
        or not _rows_have_unique_id(
            refinements, "exposed_refinement_id"
        )
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    referenced_extension_slots = {
        slot_id
        for row in specializations
        for slot_id in row["ordered_parameter_slot_ids"]
    } | {
        row["endpoint_parameter_slot_id"] for row in refinements
    }
    if referenced_extension_slots != (declared_slots - set(slots)):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    claims = tree["nonclaim_state"]
    if (
        type(claims) is not dict
        or len(claims) > maxima["nonclaim_state"]
        or any(not _is_identifier(key) for key in claims)
        or any(type(value) is not bool or value for value in claims.values())
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)

    expected_counts = {
        "anchor_contract_count": len(anchors),
        "artifact_domain_count": len(domains),
        "authority_class_count": len(tree["authority_class_ids"]),
        "interval_refinement_count": len(refinements),
        "locator_extension_count": len(locators),
        "operator_specialization_count": len(specializations),
        "profile_claim_count": len(claims),
        "profile_field_schema_count": len(profile_field_rows),
        "profile_parameter_count": len(parameters),
        "program_purpose_relation_count": len(purpose_relation_rows),
        "program_purpose_count": len(purposes),
        "public_error_count": len(tree["public_error_ids"]),
        "public_error_role_count": len(error_rows),
    }
    if not _same_exact(tree["fixed_counts"], expected_counts):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    return tree


def validate_portable_predicate_profile_verifier_tree(
    profile_tree: object,
) -> dict:
    """Validate one profile and contain malformed-tree implementation leaks."""

    try:
        return _validate_portable_predicate_profile_verifier_tree_impl(
            profile_tree
        )
    except PortablePredicateLanguageCoreVerificationError:
        raise
    except (
        AttributeError,
        IndexError,
        KeyError,
        RuntimeError,
        StopIteration,
        TypeError,
        ValueError,
    ):
        raise PortablePredicateLanguageCoreVerificationError(
            PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
        ) from None


def verify_portable_predicate_language_core_contract(
    contract_bytes: bytes,
    pins: PortablePredicateLanguageCoreVerificationPinsV1,
) -> PortablePredicateLanguageCoreVerificationResultV1:
    if type(contract_bytes) is not bytes or type(pins) is not (
        PortablePredicateLanguageCoreVerificationPinsV1
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_TYPE)
    if not contract_bytes or len(contract_bytes) > _MAX_ARTIFACT_BYTES:
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_RESOURCE)
    if (
        not _is_sha256(pins.semantic_core_contract_sha256)
        or pins.semantic_core_contract_sha256 != _V1_SHA256
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.PIN_MISMATCH)
    decoded = _strict_json(contract_bytes)
    json_status = _bounded_exact_json_status(decoded)
    if json_status == "schema-invalid":
        _fail(
            PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID
        )
    if json_status != "valid":
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_RESOURCE)
    expected = portable_predicate_language_core_verifier_contract_tree()
    if not _same_exact(decoded, expected):
        _fail(PortablePredicateLanguageCoreVerificationCode.SCHEMA_INVALID)
    if contract_bytes != _frozen_contract_bytes():
        _fail(
            PortablePredicateLanguageCoreVerificationCode.CANONICAL_MISMATCH
        )
    if (
        portable_predicate_language_core_verifier_profile_interface_sha256()
        != _V1_INTERFACE_SHA256
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.CONTRACT_DRIFT)
    return PortablePredicateLanguageCoreVerificationResultV1(
        artifact_type=_RESULT_ARTIFACT_TYPE,
        canonical_contract_verified=True,
        contract_byte_count=len(contract_bytes),
        contract_plain_sha256=hashlib.sha256(contract_bytes).hexdigest(),
        contract_sha256=_domain_sha256(
            _CONTRACT_ARTIFACT_TYPE, contract_bytes
        ),
        empirical_result_established=False,
        evaluator_executed=False,
        frozen_snapshot_identity_verified=True,
        profile_interface_sha256=_V1_INTERFACE_SHA256,
        profile_interface_verified=True,
        runtime_program_validated=False,
        verifier_id=_VERIFIER_ID,
        verification_status_id=(
            "STATIC_CORE_AND_PROFILE_INTERFACE_VERIFIED_EVALUATOR_NOT_RUN"
        ),
    )


def _verification_result_tree(
    result: PortablePredicateLanguageCoreVerificationResultV1,
) -> dict:
    expected_types = {
        "bool": bool,
        "int": int,
        "str": str,
        bool: bool,
        int: int,
        str: str,
    }
    tree = {}
    for field_id, annotation in (
        PortablePredicateLanguageCoreVerificationResultV1
        .__annotations__
        .items()
    ):
        expected_type = expected_types.get(annotation)
        field_value = getattr(result, field_id)
        if expected_type is None or type(field_value) is not expected_type:
            _fail(
                PortablePredicateLanguageCoreVerificationCode.RESULT_INVALID
            )
        tree[field_id] = field_value
    return tree


def portable_predicate_language_core_verification_result_bytes(
    result: PortablePredicateLanguageCoreVerificationResultV1,
) -> bytes:
    if type(result) is not PortablePredicateLanguageCoreVerificationResultV1:
        _fail(PortablePredicateLanguageCoreVerificationCode.INPUT_TYPE)
    return _canonical_json(_verification_result_tree(result))


def portable_predicate_language_core_verification_result_sha256(
    result: PortablePredicateLanguageCoreVerificationResultV1,
) -> str:
    return _domain_sha256(
        _RESULT_ARTIFACT_TYPE,
        portable_predicate_language_core_verification_result_bytes(result),
    )


def validate_portable_predicate_language_core_verification_result(
    result: PortablePredicateLanguageCoreVerificationResultV1,
    contract_bytes: bytes,
    pins: PortablePredicateLanguageCoreVerificationPinsV1,
) -> PortablePredicateLanguageCoreVerificationResultV1:
    if type(result) is not PortablePredicateLanguageCoreVerificationResultV1:
        _fail(PortablePredicateLanguageCoreVerificationCode.RESULT_INVALID)
    expected = verify_portable_predicate_language_core_contract(
        contract_bytes, pins
    )
    if not _same_exact(
        _verification_result_tree(result),
        _verification_result_tree(expected),
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.RESULT_INVALID)
    return result


def _validate_frozen_snapshot() -> None:
    tree = portable_predicate_language_core_verifier_contract_tree()
    raw = portable_predicate_language_core_verifier_contract_bytes()
    interface = portable_predicate_language_core_verifier_profile_interface_tree()
    semantic_rows = interface["profile_field_semantic_role_rows"]
    locator_constraint_rows = interface[
        "locator_primitive_profile_field_constraint_rows"
    ]
    purpose_relation_primitive_rows = interface[
        "program_purpose_relation_primitive_rows"
    ]
    pins = PortablePredicateLanguageCoreVerificationPinsV1(
        semantic_core_contract_sha256=_V1_SHA256
    )
    result = verify_portable_predicate_language_core_contract(raw, pins)
    result_raw = portable_predicate_language_core_verification_result_bytes(
        result
    )
    if (
        raw != _canonical_json(tree)
        or len(raw) != _V1_BYTE_COUNT
        or portable_predicate_language_core_verifier_contract_plain_sha256()
        != _V1_PLAIN_SHA256
        or portable_predicate_language_core_verifier_contract_sha256()
        != _V1_SHA256
        or interface["artifact_type"] != _PROFILE_INTERFACE_ARTIFACT_TYPE
        or portable_predicate_language_core_verifier_profile_interface_sha256()
        != _V1_INTERFACE_SHA256
        or interface["required_public_error_role_ids"]
        != list(_REQUIRED_PUBLIC_ERROR_ROLE_IDS)
        or interface["required_profile_parameter_slot_ids"]
        != list(_REQUIRED_PROFILE_PARAMETER_SLOT_IDS)
        or interface["required_runtime_artifact_role_ids"]
        != list(_REQUIRED_RUNTIME_ARTIFACT_ROLE_IDS)
        or interface["reserved_metadata_artifact_role_ids"]
        != list(_RESERVED_METADATA_ARTIFACT_ROLE_IDS)
        or interface["reserved_core_metadata_artifact_type_ids"]
        != [
            _CONTRACT_ARTIFACT_TYPE,
            _PROFILE_INTERFACE_ARTIFACT_TYPE,
            _RESULT_ARTIFACT_TYPE,
        ]
        or interface["admitted_locator_primitive_ids"]
        != list(_LOCATOR_PRIMITIVE_IDS)
        or interface["admitted_profile_field_value_schema_ids"]
        != list(_PROFILE_FIELD_VALUE_SCHEMA_IDS)
        or [row["semantic_role_id"] for row in semantic_rows]
        != list(_PROFILE_FIELD_SEMANTIC_ROLE_IDS)
        or [
            row["locator_primitive_id"] for row in locator_constraint_rows
        ]
        != list(_LOCATOR_PRIMITIVE_IDS)
        or [
            row["relation_primitive_id"]
            for row in purpose_relation_primitive_rows
        ]
        != list(_PURPOSE_RELATION_PRIMITIVE_IDS)
        or interface["profile_locator_validation_primitive_id"]
        != "profile-field-schema-and-locator-primitive-v1"
        or interface["profile_program_purpose_validation_primitive_id"]
        != "profile-field-schema-and-purpose-relations-v1"
        or interface["locator_empty_placeholder_value_rule_id"]
        != "exact-empty-json-array-never-traversed-v1"
        or interface["profile_validation_rule_label_semantics_id"]
        != (
            "non-authoritative-descriptive-legacy-correspondence-label-v1"
        )
        or interface["profile_bound_operator_primitive_rows"][0][
            "parameter_binding_rule_id"
        ]
        != (
            "one-parameter-binds-token-item-domain-more-than-one-binds-exact-"
            "tuple-of-ordered-token-component-domains-v1"
        )
        or len(result_raw) != _V1_RESULT_BYTE_COUNT
        or hashlib.sha256(result_raw).hexdigest()
        != _V1_RESULT_PLAIN_SHA256
        or portable_predicate_language_core_verification_result_sha256(
            result
        )
        != _V1_RESULT_SHA256
        or any(tree["nonclaim_state"].values())
    ):
        _fail(PortablePredicateLanguageCoreVerificationCode.CONTRACT_DRIFT)


_validate_frozen_snapshot()


__all__ = [
    "PORTABLE_PREDICATE_LANGUAGE_CORE_VERIFIER_STATUS",
    "PortablePredicateLanguageCoreVerificationCode",
    "PortablePredicateLanguageCoreVerificationError",
    "PortablePredicateLanguageCoreVerificationPinsV1",
    "PortablePredicateLanguageCoreVerificationResultV1",
    "parse_portable_predicate_language_core_verifier_contract",
    "portable_predicate_language_core_verification_result_bytes",
    "portable_predicate_language_core_verification_result_sha256",
    "portable_predicate_language_core_verifier_contract_bytes",
    "portable_predicate_language_core_verifier_contract_plain_sha256",
    "portable_predicate_language_core_verifier_contract_sha256",
    "portable_predicate_language_core_verifier_contract_tree",
    "portable_predicate_language_core_verifier_profile_interface_sha256",
    "portable_predicate_language_core_verifier_profile_interface_tree",
    "validate_portable_predicate_language_core_verification_result",
    "validate_portable_predicate_profile_verifier_tree",
    "verify_portable_predicate_language_core_contract",
]
