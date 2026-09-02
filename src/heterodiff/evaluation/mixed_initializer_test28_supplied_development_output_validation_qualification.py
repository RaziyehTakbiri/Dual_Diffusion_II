"""Bounded validation of caller-supplied CP71 development output bytes.

CP72 is a source-independent, standard-library development qualification.  Its
sole data-plane API accepts one exact ``bytes`` CP71 development output body,
checks canonical syntax, the frozen 554-estimand inventory, internal digests,
cross-record identities, and exact interval arithmetic, and returns only a
sealed scalar summary.

The five stream-identity digests and runtime-lock digest in that body remain
opaque.  Internal stream-commitment preimage coherence is not evidence that a
CP69 stream exists or that the bytes came from CP71.  Nothing here authenticates
provenance, verifies a source law or coverage, evaluates a production attempt,
sets a primary threshold, makes a decision, accepts evidence, authorizes
execution, closes a production gate, or closes Formal Test 28.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
from functools import lru_cache
from math import comb
import base64
import hashlib
import hmac
import json
import threading
from typing import Iterator, Mapping, Optional, Tuple, cast
import weakref
import zlib


CP72_TEST28_SCHEMA_VERSION = (
    "cp72-test28-supplied-development-output-validation-qualification-v1"
)
CP72_TEST28_SCOPE = (
    "development-only-source-independent-bounded-exact-cp71-development-"
    "output-byte-internal-validation;one-public-output-validator;cp72-"
    "validator-resource-subset;exact-554-estimand-inventory-record-digests-"
    "cross-record-identities-and-interval-arithmetic;stream-commitment-"
    "internal-preimage-coherence-only;ordered-and-runtime-digests-opaque;no-"
    "input-stream-relation-authorship-provenance-authentication-source-law-"
    "coverage-production-attempt-validity-operational-prediction-primary-"
    "threshold-decision-custody-receipt-evidence-gate-authorization-or-"
    "test28-closure-claim;no-public-parser-stream-reducer-raw-stable-path-"
    "writer-command-shard-or-campaign-api;no-project-imports;module-direct-"
    "io-clock-rng-network-subprocess-absence-only;successful-return-caller-"
    "payload-nonretention-only;exception-traceback-locals-unqualified;no-"
    "caller-output-body-cache;issued-summary-snapshot-retained-while-live"
)
CP72_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP72_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID = (
    "whole_seed_supplied_cp71_development_output_internal_validation_" "qualification"
)
CP72_TEST28_SEED_COUNT = 2_048
CP72_TEST28_ROW_COUNT = 16
CP72_TEST28_REQUEST_COUNT = 32_768
CP72_TEST28_ESTIMAND_COUNT = 554
CP72_TEST28_OBSERVABLE_ESTIMAND_COUNT = 72
CP72_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT = 170
CP72_TEST28_FEATURE_ESTIMAND_COUNT = 312
CP72_TEST28_BINOMIAL_ESTIMAND_COUNT = 242
CP72_TEST28_FAMILYWISE_ERROR_BUDGET = Fraction(1, 100)
CP72_TEST28_PER_ESTIMATOR_ERROR_BUDGET = Fraction(1, 55_400)
CP72_TEST28_PER_TAIL_ERROR_BUDGET = Fraction(1, 110_800)
CP72_TEST28_CP_BISECTION_STEPS = 256
CP72_TEST28_MINIMUM_SELECTED_COUNT = 1_040
CP72_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER = Fraction(3, 40)
CP72_TEST28_MAXIMUM_OUTPUT_BYTES = 8_388_608
CP72_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES = 268_435_456
CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES = 65_536
CP72_TEST28_MAXIMUM_CANONICAL_DEPTH = 8
CP72_TEST28_MAXIMUM_CANONICAL_NODES = 32_768
CP72_TEST28_MAXIMUM_KEY_CHARACTERS = 64
CP72_TEST28_MAXIMUM_TEXT_CHARACTERS = 4_096
CP72_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS = 1_234
CP72_TEST28_MAXIMUM_FRACTION_DECIMAL_DIGITS = 1_234
CP72_TEST28_MAXIMUM_INTEGER_BITS = 4_096
CP72_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT = 2_049
CP72_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY = 554
CP72_TEST28_QUALIFICATION_FIXTURE_IDS = (
    "cp69-closed-baseline",
    "all-selected-duplicate-pair-plan-seeds",
    "all-nonselected-cyclic-statuses",
    "novel-k-mixed-selection",
    "cp72-nonfixture-novel-success-counts",
)
CP72_TEST28_ERROR_CODES = (
    "CP72_INPUT_TYPE_MISMATCH",
    "CP72_INPUT_BYTE_LIMIT",
    "CP72_INPUT_ENCODING_INVALID",
    "CP72_INPUT_JSON_INVALID",
    "CP72_INPUT_RESOURCE_LIMIT",
    "CP72_INPUT_CANONICAL_MISMATCH",
    "CP72_INPUT_FIELD_SET_MISMATCH",
    "CP72_INPUT_FIELD_TYPE_MISMATCH",
    "CP72_INPUT_SCHEMA_MISMATCH",
    "CP72_INPUT_INVENTORY_MISMATCH",
    "CP72_INPUT_DIGEST_MISMATCH",
    "CP72_INPUT_COMMITMENT_MISMATCH",
    "CP72_INPUT_ARITHMETIC_MISMATCH",
    "CP72_INPUT_INTERVAL_MISMATCH",
    "CP72_RESOURCE_EXHAUSTED",
    "CP72_RECORD_TYPE_MISMATCH",
    "CP72_RECORD_NOT_ISSUED",
    "CP72_RECORD_TAMPERED",
    "CP72_INTERNAL_INVARIANT_FAILED",
)

_LEDGER_PREREQUISITE_STATE = (
    "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_" "ARTIFACTS"
)
_ZERO_SHA256 = "0" * 64
_MAXIMUM_SEALED_RECORD_BYTES = 1_048_576
_CP71_OUTPUT_SCHEMA_VERSION = (
    "cp71-test28-supplied-development-estimate-interval-output-v1"
)
_CP69_SCHEMA_VERSION = "cp69-test28-compact-projection-interchange-qualification-v1"
_CP63_SEMANTIC_SCHEMA_VERSION = "cp63-test28-independent-compact-recomputation-v1"
_CP71_INPUT_STREAM_CLASSIFICATION = (
    "caller-supplied-cp69-valid-and-cp71-resource-bounded-development-byte-stream"
)
_CP71_ESTIMAND_RECORD_DOMAIN = b"cp71-test28-supplied-estimand-estimate-interval-v1"
_CP71_ORDERED_ESTIMAND_DOMAIN = b"cp71-test28-ordered-estimand-record-digests-v1"
_CP71_OUTPUT_BODY_DOMAIN = (
    b"cp71-test28-supplied-interchange-estimate-interval-output-body-v1"
)
_CP71_STREAM_COMMITMENT_DOMAIN = (
    b"cp71-test28-supplied-interchange-stream-commitment-v1"
)
_CP72_CP61_CROSSWALK_DOMAIN = (
    b"cp72-test28-ordered-cp61-estimand-inventory-crosswalk-v1"
)
_CP72_CP61_CROSSWALK_SHA256 = (
    "6861002c492af9f0a9f0212d954e4a0008bbeaa5749c23ec9ad5cb60c2c3da77"
)
_CP_DENOMINATOR = 1 << CP72_TEST28_CP_BISECTION_STEPS
_CP_TAIL_RECIPROCAL = 110_800
_CP_COMMON_DENOMINATOR_POWER = 1 << (
    CP72_TEST28_CP_BISECTION_STEPS * CP72_TEST28_SEED_COUNT
)

_V22_PROTOCOL_SHA256 = (
    "389124f3e85b991fcd65ad503ba1899893777fb11f2c502323e05cc338630c50"
)
_V22_PROTOCOL_BYTES = 226_943
_V22_PROTOCOL_LF_COUNT = 3_773
_V22_MANIFEST_SHA256 = (
    "06b5a547df62c2d01a7869f6c27af6f35157fd81f656b452dce307e333769dfd"
)
_V22_MANIFEST_BYTES = 6_159_874
_V22_MANIFEST_LF_COUNT = 120_504
_CP71_SOURCE_SHA256 = "9be57c44592b5cb80bf68e876de335c8e253ffc1a11aa14fed2ad82213a49078"
_CP71_TEST_SHA256 = "7eaefe615325a76c16f8bb0b843bde82337c7f72d8686a4bcbcc7a8f7fb38352"
_CP71_BUNDLE_RECORD_SHA256 = (
    "c49b4396c06f1ff792d2860176a2e318612bd12ad89ba3cf6f8804e2dc82169f"
)
_CP71_STREAM_CONTRACT_RECORD_SHA256 = (
    "5aca44ab2240dfd9040ca3323b7306b12bbe6ee47a2c0af3128002b387f3236c"
)
_CP71_OUTPUT_CONTRACT_RECORD_SHA256 = (
    "13a76a7ce7b0c665ef33aa6e55c122c87bf61aa676530c984ce2fdaf63e345a3"
)
_CP71_QUALIFICATION_RECORD_SHA256 = (
    "aa25726473f54c17b3179ebabbaace3671e9815a6d3b4eec834ad6c1b8490611"
)
_CP71_FIXTURE_SET_SHA256 = (
    "bb4347afaca9e0ea41cb5b38ac74a3186b63fd95da9b4546b50de6aa1ffa83af"
)
_CP71_FIXTURE_OUTPUT_BYTES = (708_081, 724_245, 678_667, 718_937)
_CP71_FIXTURE_OUTPUT_SHA256S = (
    "b910b776d16cfe97813c821cc6358f88c068240e5d62fe26a1b30ff96937f1a7",
    "f9096b3c15cea651567bd436715a90c7c381a69de4688023def289d96798d505",
    "751bcd5ee2cca38be9edf88a94a54b60195b7c042838976b1987f5e9886b8239",
    "277476d47ada68c122173b8d1e8f9d871ae6fcb63802931800c00553657dc7b1",
)

_QUALIFICATION_AGGREGATE_SPECIFICATIONS_B85 = {
    "all-nonselected-cyclic-statuses": (
        "c-rk%+m7Ql4E+~Bj{)6f<yVTrpd@PJ*0+`AwA01@d+EfPadvi#wkXh-zzAb2BoBRf$b6}MH%>zbeRcYYy=X2TKL7T_G;;s^v"
        "#0+X|9Sn#*Uv9iLMUrS($~25{maul&C@*1(>%@1(0@dprc#~0RFJ!J9<X$wEg8loO?haiv45>jC9n8Wh1u{Hm(mR|#x{1J=)"
        "Uciwi_=vmMOos853q41O7$ag7ifo3wcA|{eiJMCFmD&eDev@I#NwqD?0qWU>>2TK&0qt&6NIvxl7$4v>WHOv~!-Q6xa%YwVZ"
        "Lof%3s^DFi*Vp@(ImH007vV|A(m^gZT!S?9T@<TVxU>I)SaYpRMKEw3})N~k^67|AK(1^a0p2(0$61?yY(>RYgB7`n1~waXc"
        "VHiYM-ZyHEJu*Rh%ToWS?Dlwas<(9c18F0r#NLEFkurVIFkikkLRPvTErW}d!NIf8y!WqU-NW2C*KEMDIx`_aZ3!9im?^rNF"
        "gN>S{#v7}GQj9eQjSs>p^cES#ppi^sIKU9WzhKztI;0nhIj@Wts)-yefYL%~6{X~cX-O|>RpP-ZVT0B>qH_Sc5vaw6b4Z`@^"
        "LiE4xRh%b-#~=ZJjjH?a351(E*c6(B}gMuDQ6{XsBSVIoKM`@=p2tC2n<oDBgj=p^w4dhntK>`W!<5`Ys)z?>;qHQGh-TWtr"
        "gP6z`3QY#7V=F0SA(UPgI)WRw`yaM<<U^1$>X&I6b_JP);htspC-?2uuW{jnynFPiZKp)tI6*I&!I*5;1H&LK^{Dgh&9?hq&"
        "JQ0HxqCm-edDuDrHLck6@d58j(L29o72`Q72p`#yJ4Skt_pe$$N~j8>-5Zosym!moeF<&6&Qi8*OKNTns$%<90Aw8tF+$tgq"
        "u#)u|y4@LsxjC0WdIw2$qWwzEX;Y?d)+X~A*$=j$FDqb}2<9wXd+p3{yy$%jBR!?goUg`_q^4+$~aj3onLCax>*f@ny>i6-e"
        "53%*<m3njEGY<$o{PuB|?Z4d@<#(aw9lE0>G$R>$se2g@P2TZ7D)9$RDpR4kxb3cOpDm;Znq1PM`TF%ww;tpJ"
    ),
    "all-selected-duplicate-pair-plan-seeds": (
        "c-rk(+m75e4E+~BuL0{W&94N3K}l5BtuGT>o^~7L-%HPBN0Z&O4bnaoFvc@BEs}@iAqmWv%6H>5bkJ9a54@4~skwfBT=<d4|"
        "IWW+{Nc;E{i(0u|L<!r%G>MXQ<V_%IwN)che|fqRZo?yK0a-NW2GQULA?q!-?W&%os<rCZ@agD+Zzey?wYy6HEURLq8?6)a9"
        "9zJ<!2jvIWhMG)^NE=mjh8)Fe_dym=?;E$yxJ$a)nY6aTy6KFv{3j8B}3g7L^yays+hkEiY_EVcQg0KJc_tvs1HEvs1HEvs1"
        "HEvs1HEvs1HE^Y_%yf9iRfa&`Dp!QAEN0dp7HJj1x8X&%~X>|d%wo>zRT!cnspm)s37#x{1J=(+8dwi{14=4pOuXG}Qb81OI"
        "b7Ni@2ETj#6_Xo!6kf2{k@l_{G>qs#vCF$kw8RrptGDNbT)|uR&aPCr9n0DiF&FyiXC=}QNfHgnkh6DMH+L8%+XhRRnLT*T<"
        "o5t!;1?YR6>t#J2dvab=;I2MVkg=wyNHnaT@e)GqDaJ@j5l`4p$AQ3V|B|u3c(1+%n}(swn^wC#16P{xR1=M6De9yhN(;_G;"
        ")uy54FQEk!I|=C7;iX(7?U^F0&*_ICU5jlbEJw#;()3Yo?-liRM$YS?=VrtB*1YQoC3+2;1PU^%E?G*-X{p!XoJ#7>9{pu0T"
        "2XZO53P_7cf-dUodRty1VBQB^S;rk)#ID2mxGbniLWmBLYo_*2eiHxso2d5Y~DhlS8Ko&KK@y{Jfr<YFzS}#XCq+UZkKj2jD"
        "Wr#D(-)DixUvmi(A=PFC;`g!7>>!bPi-qIwDIMFDc|BNDo;sg6C2*Uq{@*@Rxu>?@mCLf)W|*6}1!DrS^Qx@lY@o|-6tGDP7"
        "U4&Et=iU7SWp)&X$w{a?S5kZ-llnYUjli)FO?VRJPL8-Zm#w9DIR|FY_LoighKsOt$+ggMGh=;gdcz~R7IOg`;r(J$&k)GCv"
        "t}nE=-WaGYuPuL7xYhkScY+&j?{B|h<2$1@lW8|#+fU)wf1+}q0xyXz<3UIzm}-m)3>9idsWUVoa?qL+86LENhE_l0#Hyn)K"
        "rZ#R)t2x~TV>k{%XN~sQOy)QxA$=_C-t&wXj;#MLlvv1HB(*c)3zC}Tc#YUcOYmvTp_laLdf-fJnF)>{=5=5w>|TK(8F(Uci"
        "HvqwkY3)7B}dQme3LDhmyL5@j&tw?`<c3hon4Znv2Ws+V<H}9kg|dbF068{S!Bu#Ip"
    ),
    "cp69-closed-baseline": (
        "c-rk(>5khr5Plc^wgBFTUu6*pJce1dIvk1Gb{pi~JF>O56nmR&f}q&IuqhA8nfd0n{kiaU*SEE6iv0s4!tBWMqC}7#lWemn;"
        "T8$LIV3wt*=DU29o2BI&g-axbA3J_J7xH?ZYjHodDFU${adwHs8@EagpVXsWV4if%Ui7M_`hBo52Ssg2Xe>RyMBMz6$xCP2E"
        "fvODCVRVyMh)Ub`J&l32LsK+naC6ar?ut-PAO%KYnlT-o@iPVzC^v+s9(PF+ZKh--UWZ3Ert6p*E9)5+-hMO8hFm$VhdjUpp"
        "_qaUoY1?6l$1i1Q6)Qi#jlD+b^4XoGxBpY)X*uwNhO`w+VivHQ@u53%<=#PApO(D%96e=gim=f@Uu9jZLIZcP2qR(;nz7yCR"
        "+uq(nr(F(>~x2}s-tUn@M)niq6PtfIlc&-LWFhCdJKjcQh4+I&J+cot+5Q}|s&4`R=p3qMn+9ajG!@n~Oooi4KP`aN6RR07+"
        "o$8fn-5sV}9flrFakBw#%8xMPxO~MnW`u65(716#HONx;U9m5MYZ@5JaXK6tR9>RtwtPY(V~JMbR?~8TlL@6q8zVABc!H)sv"
        "<O!E=M3dZd+{|`-?nw0xvKHe&E>T(92gO}vP26D!A2UmWy%n%hzOJ=Zwv!)oD*Zfr9?nWP{{<Fs6YY4=!b|AkC+3DQh0RTN5"
        "HrSJifqaDLj!zSsjDrOejjJWL{XKEt5`AAsI=*ni#bbQd7>*63S&H5Q2#-7!2?q5aw`Q)Kkh+3RF48RAkDcD7A?Q5s^m2g=S"
        "uo#6gK*fIIY2hUhFqk5mA$Qa`|_=~z_Vn2%XJg9Hyr^Ca+(KTkv(V;ykq4bx0=rilk2N*gUAH3+VOQ$mShhJ@s!TKjOUBiz("
        ";Q5_oBEtPf7ipLO8#e@$;Xit<fUTe*`je$~aY2*+LNy=Hrsq@K7s;K6IXivfNHB@%Kfw`U5zE~nK<$)V1sMM%G3Kf!#=#eul"
        "dLDhWoO(`z_gXP<%%&7wOv$;B0s>$j;&jS`%Ng23u8wtD=jRHLnl@Fx;+|`x#j;#Veqnft`_gw9P-QNsUuEN!)*4W>ZlP-W@"
        "aOlioWmhKMh<i7xR9JmqGh0fbxtif3OYpQlwu}P?-X~KRZ5w0U>W0p#XJwPF+Ac_nWw_Ibn@J)8I5P=($4EnJ&hXd)??#f#L"
        "9lk7?<*i&iYPMX5CabAaFP=5OYjj$mOLy%9U*SX~NvR%$W^B<NmsyWy{^mpu7pqU!ZFoLI=PHI`v}4CdmulbtS%%q}*rhi_`"
        "3y=h=vJ7_*|J)L*{*3&zbZ;Q"
    ),
    "novel-k-mixed-selection": (
        "c-rk(+iv4F5d9ZDM*#1a{K{e>P~>o<R+hXHl{Q`Mzjq|d7G*ozB1MZXV8nJf)Xbd2xzYYs)J@kP8rK%jpXd`KLO+q^j}j(MA"
        "18TvL{~v;Tr+(ZGsC@EX0$W;Pm!eBy(u&Q;Ek^N`!Du0ydDwRzdk<|5nP%Ez#jNi(Bi3}s`&hLTAF3W_nTr_l{C}k7hOS&%m"
        "tkbHWTdTf9DFH+&DNPQpKg*6b&_-3w);R_H5@7pPB3koY;*Ar$lA~rMa+iFGU8dn79hlBVzwf#4;D<2C8$`xMs^TKg$-}{8Z"
        ")UnDVRbRa;)MTvp_=y2{^=`0{&n@3NJ5$@05g^<Pjex8+C53Wbe#nVZ`zv)d^IC0R{oC7stu7IxgX`~A~WQg-2OsJ3}+n|C_"
        "pXGp+@I&r?tFEq0x7;5DYk|1tMUkUO~^<#U}`wf6p_H#h)MX{SZ*#ZCe>G;SH<CJCnz;fnN+6$wMJep_qnsLJKWtYR|!AB<f"
        "wAw+44MI^%cLRAd+8s>iVUSznU2oq8jbuT~=WeFHo9SidzRY1yTIVt)HzsRgQ!XD@!sAMKTnUdW;c+EAu7v%SfWJzIzE8#Tx"
        "55ogdO1L9e3b^*jj<mNRo}I5#d8`acq;r+(F(@Y99$Qw(0svl)r?isy+W7z;jJ1V!T_CzAJ~n6{}5zEZPzw`Kq#K0Ye!VP=="
        "gr>kdu@GH-Aqsbgo51K<j=Q(ETe6O>8pLraMllIu1QjaWeror5BiST)I&k6G9&<-@0)`H>lF|UGZFa*S0W}<8(Z>=)6SYwtP"
        "jBp+r_FYFZ9(qEObzF`!a_S7`g=0l~`pEkSwmUR;CqheMNQt!jL6Oe(|^PEs215{N2#L$tA0Im(Fh$^$decupNNLUW<Lkwgd"
        "1Su{@ZsBrQ)#OQ~B5f7LHjFNwG-50>PdfeV%43{>Nnlc+L2{jgdO+}D~7{Oh17N=tjwr123h$M0wxD(a`fU@A1o;t%|fPVo$"
        "hih{mBM+Vh>P#JQW&tO{P@yCqr}k3$Xtd(i#G3giWw44-E`$Q3>loxRna}PA_&O~`)s1P%;su0AkXjg42d#<H+9<=Flr9FtE"
        "k%JS>y-i`9cRvZ>I9F>DiXc4(%TGVsUsAcxu}k<>(<ITLutZvL=S+m@<B0Phrqld3PWa<R5<b-It2rv)}TNJsG;Tz^P{P-B8"
        "N(@Zeebx{45Nj<TWSSf#b#pir)#O@mkIi!3=rAZPdILAe}X;c32i7a;61n3kv||Axx({xRl^<Ox04SO?s;USJSTQGwr!H4p^"
        "3J$*&6MxUYSOP|9q(SJ`-{wFWe84p6nd|Ml;vT*4u1K{VI3<3e(ZQIr^a2{?7ZQP4gxrxbPrt+DVO!SGXN99YIUFrntzIr<l"
        "zD)Uqr*G`^WH6eLswsy`t^)za*TbIVch?V`6FfQfmJnGjelQ-2J2pkS8#2i!SQ@OQAnc0?KC(O-x&g>9c_uK6(Tc4c=<y~lg"
        "hHh{O9RWY^P-hyuB(He4mH1AQQlGFdPP1#CXCuyG>^Q}_`TqS+w4a;d"
    ),
}

_QUALIFICATION_CP_ENDPOINTS_B85 = (
    "c-pm_Te2KEjzsrT-~B-n1Rt}NvR=v9?0wEbq;??6N^130CWFMo;cz1U_n-F9|NQ$efBxs6{?C8^^Y1^S%{ABU*>m%kd9z3BX"
    "T=)X_l_02<;^={oi%Qck@sf1>ukQTqGz--qPJwpSp8%h`<%5_kKWt5XXTA?dX7Ht?mVwgzT8GTt&g?WSR<nG;MT_6<FH^K^Z"
    "fJQ|GGzao4t+0NBrFCdv%s;bLQOpwtm-)WH;?Z<UJ$Pf8#;@?wlESv);X)m@{6U%VBo()o-$7?snO9J8bH<&Ev<q_sq3&&F1"
    "g8Gk2cZ+UESMwc_4bWxmO-uo@5Bd$qamotR^^44yv6jUESMapX922m81kJFMBU$c)k34L-(CIvdP=E~`w;xRUSf-8(y)cW|b"
    "daXHPv=<{*}j5?aXdD1u@jGd;tKK<gK&wy<DXTv!;=oowE80F-98{RxEQnL^K|4jblZwqS<<3V@vJ+>V4oT1b4(tcyhHFy-e"
    "HyHTt?!?}~W^Hryj#(GWujF9_YC9dn5q$$YU81drzF*rY>HCGd%bfj7Ab#9NU`!TmIuxgj-Ca5f;J{Ag3wz=Wn{Sg#1W98<m"
    "(5}1r4u?IB#qeXICq{lMi37yjj=P?_@1QU=q$V!OK~tGW#Jeeif_p-qGB~;;NU}C%vs8s!RFiTV~;pyIC+tz10Ia6gF6Yc=h"
    "QMTOzy4WKe7>ml^^XRG~7;#u|byE>_35o7^LjrY<!nEU1lb+GmQKjo0RB_@QGyW*p)4{hD)((<L4aUXUY*}%E5s+8zv#C`F;"
    "}4_<%TA;=?}p0Do`Jc`(W0*V;FQB)kNw@Fz#Zmwfl{ClRLXc_Pi!d&uH>Ip@Ls?Bjx7<y{WD_<MJCw$^tGj@}nh%)cMJ!d6c"
    "Q9{;|xKV!}>E?JX(O;$K<ZQ*&k%T9D25x0Yq>vRvz`9N@hsDTMMHFMw~juGH67~P-5CB`JE$S_RBx}5~?VE6}^1ne<47HKrs"
    "HZXJ;`Ioq=Pf`-&0!sCh7O#w%KVx?C-2WQ!$g&M@A9DQqP~r`|p~R)oI4DY#MM8XOJ{MdSlNVzXSockm_dS5Ds>S@tB0-e$9"
    "Wtd`gGtrX+~qLxDMwV_MlEXin$#lQh<FU&DbkM$P@FO*A7^JXJ|wu~5(hXNa2SFTrIT0<R!hP_gl<C4ZiFbg1!j><V*;75k-"
    "v^d#wF*@g@agVY;u7m7e-n}C)L7-U=EB18f-p+YgtG)^FeBPxS7sBjj<oaW!$fpV@ezh?ZH!HMwN9SN0;!79h5<nni>x}@%?"
    "lYVKAm1$BI0QRHL@Wn_AAvISI#PLzuy{!8<zV4`K~e#9NRwLQOg(<|i?PwLu<`fUIKw_=nJ~9a5;IA#f&4g&TphOPON3gTPP"
    "W_23068YsuHNIia2PIxAd=P1P92OQ&P%-Q}J6V6Mn#@X5wKa=$qKX4FtbLQB59Rrd!i>d@(wU7F40%KWFsS7-(=Nn^+d=LtG"
    "Gbn8|QmV0};37NA%f4E9bY1PnQ>aob8M76vQ|Pe}*fjT}ET2EBP8t-`Bt!#lk7-D%%`c9MVL0hdO?HY6!IB`BJU%qqz&w%?c"
    "nY;EU(rnRraBYy+1gBs1zrS5ueAtTl-3|1NpJuT@IEI2BY_vTNbJqCMA+M2(aiCyKQbOR5Td*ICDSRl@~kN}TJ%-q`vmFmIu"
    "yg0$9_P(pTOD#4UzlCl=O2rG3>}-vP+Bsh~(^thvMOnv`>Nc%8nMn+D8ZZi2&+i^^1Lc8+;I!<7<BS8J@H0;WrP~aMX3mH}>"
    "NYZg@*I>1_s1Cp35v@B*`=QVC#97H4<*#*&~vOOZC#?P9*tU?R;XmPll0lpz}P8PepGd+?aB>f`+&6a__C$d}?zf^z?QpJkh"
    "flQg_o>z)9=-Ccs6DHeRS9uI-YlsSAD7JYUHL;y!YY24A?(4wtoL22O;a$IaPs`gVNH_L)iA%T~&5vZx}uMu)mNWj<>Rzijv"
    "!a1K=^FvGmb}O0~WB8K|bbrrsYDhtNFejy51hz07#)N2wBv~pqDS(T}U0;p|JK<n<Mfz!5_`_n?usjy1e1m&ksE!ZBq!DGoZ"
    "GT1li_}>8t31bA&1s8^B^!We(JW9c#ih0&SaxIVp%*@O*%H1<Io^?%k-t><{xHQqQnbiVyh-W;%;fCq1X7ngwkqy|4JC-<4D"
    "C1Zq}?X51<x2(D_Jqk5Y6wSB%h}!4RK06$0&rZ-2{n?)f=fz++GzeYC3HA97{VtYw|d<1vUbDYLm<-E&2GUI+PON!79Xtk_>"
    "LIFN%~KhuSb)aNkzq(n%<3U=+0(5*deb6#5W&+Uai^a;WYR@>q9E(T3<vT+UHC3%g-8f}W+w4?Jsyl8?3mP%ui@5fyCmReqm"
    "O-Y|`^8bRl(yHr1H!J?&)stSRBa-n6uSZlx|h(~&QXl<Bk=G5JPp9xovAC)SVG>aqN!K=209F7A^hEz8(tu#puX-MJt#hK{a"
    "g3S^Vg!XQaM9lcrou-VXpHi6`qewokNjp9*(~kSVlT(pRaTxc|t#ADsN*b2do{#dIfNFMQkTBrHPE0|S0>%jyi6I@O5`vhfK"
    "DCfC22^QU(oqN|o0JRURSgFMK1QU{B2`xnTBS;}2TasdFX%5s%vL+WYP*UM@v&8sOdfXWo~+ST!~cGcvv;ZqoOa86dC;!Qh6"
    "{QrSxoD-vdpd<f$dWX(x9^(>T=-Z;XGYv?ERTF_aAF+Hvwdl86<>V5I-V0XlqF$nI>^b&NTi7&>G5cQvn%F!lZOc%_d~7H;7"
    "5uqrUem=!I<DwPE1vq%zQzn9+)Z0M^3|R-{(~(?<v~fQI%}H;yNzXaBTd$~Np`*z58ept5x(ZA@>ru&!DfUe=ZPj*J7{Fdtx"
    "d#W<q5nQ)If9#^ux<wOcqX#<Ai>~26DHH0lo7e1pF(W0Vzv%hWLXMj+UCNTI>Q1YWcRXhS_k#=B7v6gUCG*i9}u9I9i!my}o"
    "DcXuHDS^=|b;A5Gv#5^A&zmcX9Ns2|O3{@$P^+uWBEs9|ACGKjDilJ<l|7PByOybA3mNX1kdTPJ(lsa>zxy8W2BLGMXSX=qk"
    "vw2dZwJVcP@>sNm1*$fa&P!7lMp1YG{`W6_1B;M^)lWi_yfXts!1e@7SYHSX=qf3>1Sye`ocVW*!E71#D3`n@Mv#Ut>kl<{S"
    "hhp$r{$lRQ2O{Gzi}0RcNu0*T!QP6D9~!g2%_pDWUe^Y3$8ef4?a^)k+h8^fo%^s-ENLX4M0*)LZzA&=0><p&_Yc%Mv?|4i-"
    ")=zw(t0X$n6xVi8FMm1KG!&WaRcXvWFXeTW9a#M}AiRp1e>?c2WlvtF8pz)Jnu_m!*x*BYt?+p-7j*`2BaTnnPzZZTp}=0o~"
    "WaHnn;CGyfYZG~gi8D1H5ew>I+isZW<45H!HS=T)RlQIzn>)P_F#sn}3{iTNPl*SR3v?CV0+U$N*#f5Hp1K#Xjn+U1^?WikL"
    "u!5tiU@hC)UYUJV-pTk?7u8|JmN(wC<BpU3qH`XBZ<(-aKQ+ApT!x8%;0lMj10d0ZIUundE>NFtj#QK?k?p7w_pgh55S<>M?"
    "m(kZ3)O^J-T4%@%r3lF+oj0CZ>adAWOgby{$CdV76tas&O9357#6lKHm6;-w+vH_*K0{Y(vbs8i>w%4!4ZxvhblTtQ>2~g0U"
    "Nwck(!Z=?GbSP@y}7qh?)!Xl21vPO)F)NTf;>_WLCLn*KA`>H7h<sxun&+3QDiqAI$l?j7+Jc=k9uu3jA^PX)RuwR9H=QBCq"
    "#2f~1tf32X1ln_gf8TLeS=^|>dF`ORm!<@}0f3DW?Oa=&8X(j~;?aY9F>NUG<hIsF8*=q|6;Z}pnmgM~SsTJdOa?)9%@Iy?E"
    "F8q-lw>%?gDCKcD!&8p$zCG}LW(b*LGoDS{W?R_<_<MHu^%Yi~aOY$YhHf$)Dl+2dFMqLFfmd7B`n!+Y-zc!bIh=-ukDrFLi"
    "rMvDow76Tb4SFh&N;V8~ss}3_RM7HxUFki_s5`)0qevWugTNLoMRk=m_Nzq7--LvB(yFb%`Szl8D_AN1lj=a_kfnp|v>#H{<"
    "up;IVSXH=!ORYMD7ylqk2*HxNpe==J0-+Jt-}Gwnt96NO%x>TTlXweYi5&`6z!AJFT?0375?>`Xd1LXwxl&K`G8XiF@z1SOe"
    "b>qI_R>!uDr#A(-w)Ky>*SEX{`VNFCaBv3D~%=#8!D{SbGW?y$1mDy{fzl#9`V|$pO(cvv$cE)8PrzO!&I%RgVA4CFjIP%e3"
    "=;e`s?k`EizmCBW)N=<!roXu{*v3~pVd+oQ8S`Q^~Z9dGm)4PpyKQ+|{bmeWIao1s#ph~c19>?1}kC67f$kw+%ka#lqh2loC"
    "^&A&fvLXG}KB|nAcrejVH*y3pG7;fiygdJf-`g=hU$3|DabYw*;am}Kp^kXv|uV!$`L(bt`sM7;iC?`Cvzv`9t8(Uti3_p1="
    "-zN}?e|p=m)`?-A?8-L-WdOq;TXH(0hdnf1OB#Ete5@sooHR#F(xJiTy=B%dfm1##JRNL~YKLXkuQEJ1I3I0Gsw=)sg<c1nh"
    "vOqhp6s=RWHME`n#8$c{d%QBdv_#tpJw#;GyEsV*n*j?i!!4Y$TKkP@ji1ZSP_z~<YErt%;RcB(ue9X#sdZ%+s-%hqFKzF$E"
    "Q=OiWoH5IB-BE=BH>ACpE|@A9B!bs4Q%yK|bNoC`~CC^rowbk5W?E(m`LkaVJ=N4YaX^A?TRJPLcFxZOoFoWEtKPLs+X$855"
    "Gbcr>Y_P@TSA;LSa`NJby=Wq93eeWe6akG=1!ZKP8&WFuMbO@&2ws^{1|z2QL^?~6yG3#&T`CStIYQMd2mJ-aNI_)|crJMsq"
    "D+w}yT((y9EW;?~q!fm}WW~!~29!_@?TCId?8gYm3LWcuv4y<<@9ZO;QR)<YnD%gOX-czgSzo|I!yG$YWo60Z^%yr!QIP;(?"
    "BW0U411eT72ep<LD&C*kZCNErwZKx{7Zoz&iPGv6mZX;?gWS?v4=1rsjZR~EizDtK0=E|<>E6@|u$&!ERM&@1;d=9pB|*GDQ"
    "OSDYsg>AAP1C25s1RVW-f#=MG{;1a;}41<%?7qKBTh!Fl0+xojNA$`1aVhbV^s&Pju-h9oMwGKH9or4UuY(JDa4LL!HksVs8"
    "6GMhiq@EP5vhFFbj(tQP5W>s`<*)iaeZW9+P{(a>&Aihii;+b)yht6@q$gwY;-@H6+^YuvLJaLSIF@)E4X%91HEf2jcXi-L9"
    "b|aZ@ntzL{jpZb+qIwN^ed=C1(<{3s^P8*;u+eymp4p!9=v>r_uT5)m(U6p#E!y_V2@@Tz7g<a6(g>0}U=Q@b(O>VCdC5qxc"
    "EAnVRv;p8l0;W4e@L~;5uot*>j*uKv4#F*=Q-$RMtX|P?xe_&6uK@imIjf!v768x#z-&760&OU;cUQ~6N8js{-Cm-FIT1XW1"
    "u|!wM7}fFDRi6DnIkGfa^HQ`Xu>4CZm+=P>L@z#T2kq6U&dQ%Dg&m!(fMyY7$+{$iHv)-viFMN)6wjl8CCPQ#+VKhHb(}fs="
    "09JV(phskrDAz=;J-O8I%kcG>CjQtW7i<us_A*(0OBD-AyD+h1KGzTU5JkP_p-;dUvPeaO6!z0eRih+sF}iYEXowzW`W|jH|"
    "n>fV9LR$cT<P~8y}PXQP&t=Hp+UA`k!wdI4S6gmf`!&k3cMUjob4~hf2F6aa1M8DSBAxWyP-o^EX0f3%FEOlvl`L?{v0T72R"
    "P3U%u6F)Whc0pR|MQE=HgfWNg5Usjfi4dc-d4wbCUCOJ8bql%yEsRUrpnZf#V_$YF0=9-ZBsZIf^L1s30hk1ys+_AkjLm$xP"
    "di85miRF+F>5R7@0U0S_nnD*hr_g#TylONpll{1)~G{Aw6C(WZhjIZ~Q#lDC}LQijK9V}BNhhVT`u{RQ#{>ZCSc)gSsEbSH~"
    "Vs@#^zR@eeyALmEZZ78Er`u!mdEYaU17G|)wVzi&8}@Eo;a^|>VH@BV=eJ0;dWmYy{(@ajF;KgfL5Ft^jzF`z9B2Ac<Z{|kS"
    "5qUaxckngl=nFB*d6HbrL^3SW_2JEzo-o5(^fiQD-(JBs3^`CG>Gr9gN+U+bXVw$KIqg`rY|Y^?tmY&2E5TL>*~gr)#2O9ek"
    "8ANa9a4bw>%Oai~7u2gA%I-W)!iBQmBx<&#~qF+f(Xg#^0@;uOlpV0rpw%kv8u>m9N4{BHx`+x2m_&d|}2L)Zw+hv!VikRjS"
    "upfUk%p3q)NUt3J^y_<{%7sV+qRv8cTzYw$3q$cEY)WUk44d%buhJL<ky^Ws(F|NDQx>YOV"
)

_CP61_ESTIMAND_RECORD_SHA256_B85 = (
    "`0iJ1iDj%;4JV;rIW`(_$A8r3&EVSy`(77m>#M9ChQKN7U-I0P?h)+N58DUYHd}$9t1~kj>1Qe2uKzT~6@iOV%6jSnqndz}t"
    "rvoRQ1(ExKCXj-II}5VnMX$ISS!EN*&d0I*S(up>WZVe|4FK_1ikNPF)?BNXUy<}1?g-P(~Z~8tTty5aaE8CmRb`<<@#_Kuk"
    "qg?V9WiX1MK>bg|rSIp0*je_=qGmcT2=PJF_H$xff3Iy$2_}@zLozEx6Mu?A;!H-51jGF5I2fq3^$+_}4|4f)G-Z664hTax*"
    "*&M*yrv{5d~0PGD<Mz8~YAkC8E|21cx17|m;n{1>*_5PM5SgrGJtO!>b$16V|a)xhpbogpN`%_Lovj_!M4{%L4a+;vw^;Rg&"
    "s@Q#2!HT{MDp<45pj76DS2Rn)`^Dc`|VI~MEl6L_>K#2m&WL}{h7*q&MX{8nO9Vaf6xRNY$89Iq)U_+)NDLN!C<mi{l5je_l"
    "cZmg-oIK)rWf<F84sogoEd-=5wpsCaFRTWcC9p}K#(!AP1v|n5np*>Bl^+(C*aRA8e=`~&`5+gi6W`o*NrLaEZC076?JPY!x"
    "V@Vq8Vshd4UPGVGr8kSsrd3K4M%+GuDJj^=%EMz^k(zLJv_bSo|1V5P1P~z7PCpkjwPbj8YN7Hv;Q69r#b#mlCn6OG%rvav-"
    "^OVqgqRjoPbhH=7+h%)%yN%ATG*hbwtH_wT|_!Mv8B{FayGPtA>P?_DFNgLw%a|r_((9=ef-8jsPcs(has0{yfkKw9j@uD@U"
    "2l3h5bicWPE0CXl(AE>!ljI~cWR{Ml;ShYqqXH19HC$5hXT<!i|Z=+Dm8qi1s4EQ3}!dxGhT)U@e8rP3mMO67X`e}gm%YY_H"
    "rf?KSls02Ub?sf1TPnst1UZC!P(}ltihaIFgA44z=SA;Y4J^F@s($}JU=<E;aU*Lr;GpnDVE&3`6gWkH<DIiC<&sKX>Nn3N>"
    "ggUHdTia66;8$<-!I3dtnRaVl+u)$@0J7*)bq!&7oQiMNah|e<o?azaKA8Ljgn(CYC&ZMkq|}y?1}|96#cIs1B-MKkhW+PC5"
    "h*$?m|TE$#qi(IVeYNn3A(BwI(0(Vuet(=NmH(y=Zrc-cohBFMhr4j#Oq>=(iXeHBs(^|_W&nZqafo^1wA*0cqnU@$a^m|>n"
    "P)P&}_hv1{?nIRRG7AAo1$6H~-Z5KaHz)aZE)_%TbHs2S?sB%}%9?PqjD58Zh~ueGJol9*pc`e6w;jANs0-QiDS=D$hY?%n^"
    "H=oC<*Z(Lk`<5xo$vW+$Qsrsnc;fra@#kE}}db)4sFzVIShuJMc-7b_;v)1NWEGGrAqKS6(+%TY;W(EMpt2`geAP7}a>e8Pi"
    "$j#S!vGWiXY)@3#6;qX8cyov$ID;E!k7$=7zQrm$>F~Z)c_qaJqPI~VbY9+AxM-`ldV^2=Hr05ZdI?Aeh7g3I@g_dTm4v^si"
    "I@>!KNGec#q$ZAw7A~-*j2lip{&N1er6UqqfSD4!y(!EHP*<!YXI-&|3cgY3y1NR{@*YbE>Che2M_QzebD-HRgS-oZ0kXI({"
    "P;j#^K#|oozfv1m7*X^e5Vw+A^k7Qr6z;^O*pylUDl<?r8-xPHG2X=A(5$`=}=a4px#caAW*&})DMyTMh+NEjU$fj--PQjg$"
    "d?u!8UW3=4RjA(1Qe%)Gu{5qb~QVG`l+EG25nvVt+T~_{<;jTdU}{?RSp$Ps}i20j>2dd=v#lAeRpL5=`J)eae{dbF=yeF#j"
    "^HgE2tJ{%!c%MxzY>KV6(-%ukd*i`%Xkvh1lCP{EzrHZj_ZK2LP!Vj!H3=Ppw+L<uNIKix!1j3jZVp5Re4=7Kj}c8c*W!4;f"
    ";S@RVCUst-OV82^^hqbkQU&1t{loeD*aQQ|!_Q)l_>-RbJxK_{vJ!B~lfm@t=cEpvJh}hsp%+)rnH~lm@Zo(c<mK$E_p+ycG"
    "?n)f2%}CV>@l39wg~g%q*sg`f*v^_MzTMbFG_&jeVhxYL+1J^dD6v=$8?5;aTHzsvWk=`6_*I6_x?OL-e%Vfyf`FzBkFxaZ4"
    "P!fk2Vy@?xcX7gW>leYt37i7h_i<!t?LD+hGuR>P8^z5L4@e;L0!3gv00uax=r4naN7X?+vO_SCUr`1M6ftAAen+`!n|&c#4"
    "@kBxLK4|Lj+*^tw|7dy#w}BY9nI!0(p~{v|RKbyj54#M>{ai?9!1nUflfVnS3~hRh85L1qvRn%%}Zf_?3OpkoWxCHCv!FzW;"
    "*Myu*+KkC9VJjxRMbk!KV{`|^Ybi*1@R%kK=OhOcIrJ02`;nlW)|)Tq}pi(t{p86iInh9`53?L&<^ASHL{#9f!mZzHILvw<H"
    "wBiFl_1Z3Yk1gsBW27ZtN5*^9>5cu|PSoU>ocElqTQVS1+fl~2Hn`f}Wpk99L?vQ_Nk|VF=``;EO?jL(FwLQT%F@vaBB=e`>"
    "b5v_5iZg99M5K3bWC85cEslQ_FC11R+<Yp^tio_fOnjmWb36lVx4dJ49l59=|1a?erxHZ(OZJX<tq(+$B3T1P-L~B<B;{^f*"
    "g7GZ4ISL+uma#Gnto7!d66?g6nS#>a84q6xpu0FKg|j#g3-HM0&^$pdQ27|Ck;hlH$#pT5Dv{hd~C+Z$b=QCfKSQ=3UbxJ`D"
    "^VMCIp#z<ZKeoaz|TI<#$83nhg!&P&5_Cp$7TWT{DRb=vgz6Jhr0kMzx8-oUcZoqj<y~@|!J_lje~*+Re^<yNY4&;vi`fv}q"
    "mf4Dg?ys_V`#6KF#C^)NSRb)RqUvz-wtX8{~B2)!L#*Q7>l;2F{f846jj`dJq`%{p?|5nn+8Z7#!HcA3VdeD-;94FkE7wUq4"
    ";UI1U0E5rc&K||XJX<D>@gI6i`yn5qeU!;SlGxDLAVHOkA<OI>^A<pbPOfw%Tv?A7|?U<Np#{hIsX4_^OS*qy}67_3@B250v"
    "*DAyOayi#BmQ=v<y;_M#e;(p8ex^z*eq5nBm1Vp&ddfRu0ZeaRhL|f5BsZTR7LFbCE(n2~2APoDt_>qS9>Ro6MLo|2-YEsK1"
    "#wUBnyWZa;NVanCf|yyiYH`c_jK&|j{dqr+v?{)M*D$g)u$*LuxjE(zF76yiuKF!6--4Ll(dq@y_#4dn^2M<mD$eFGKp%I)j"
    "fa7E#lP1F6?6gEC$bgYUm%hkG4=L-P)_oHXw6~tRv21n1Mn>#$d!GRjs&j!tyRaz4Qh(QvA0@i6z~vC6uUi>L{cu4O|)k$a;"
    "c7_!%UH$t;5%&7@_j`KEEHo#S;Q`u`1VK-Set6Q4aFTA<UC=$abGK*h#$HpZ9?7nY_P`{}7;x}wv)Ro<na!-*Qt54tP&myt|"
    "SaNsigSwS$Rwc-_Nena(8iKbyTm^kdM-W4w7o^H1X?0-RgGU?UxeUlNprUO;Yn#5Lg!!sQoeWt0d)icO`#k1ybJp^x<L96*J"
    "Df(y|HjTj9KvY}A<S+xFyd`zD4O=)&G-Wu1k1jHS!lCI*_rU^<6C~x}(bgPfTr4++XGEyW)uz}UB+690NDRKJfAbLj*_T40y"
    "UR%}B(%!M{q6n4j8_NMtK}%ZTN8H0%LN7v%O^F4PJ-;ReQGVKbqf-n-;`145}S&+;lko`j`sc$^VImeOa$r)&~K@FzlafBUA"
    "3&FEGNV!!-;|AT*3lO0@}aBR|+S4Le&02d;MA;i^n<;e6sL8?k3+>2N@~hCPvOg45w?xzu-TwTN#1fC4pha;Tt{;dgvlANI}"
    "q}!Y23(mUuWSQ<9WNBA)<h5THO|sg;2mm?YP#N*Lilx(9HDkclSRd{I=@5uFtx*-Fi(2KdDua=f}P#%?e6deHX{qb2;C`PWg"
    "jsfb)PZUO>>m6&}*F@g~+KyITM+>_(NMz=QU)U2MMU#|fFuo%_1TjdEi`MKt-NsR33<&ayo>_d_8rCmt=Iw4>n;=$%^CmOOj"
    "&Z0d%=Mcq%*puh-z%uP5aL>JJnpaXl0#pQCSJ64kQ$GJSY2<i0uKtKqNKMKX%NCcwQpOw`W29|jv@<jqR3iYfyqfc2c5Vc)_"
    "c|GqliY^nhtvA~@QtG)Xv2AnGb;qrH2CK$f2GD0sF2)GkOpS$#Js@)`%N^}q&f~$d{)B~&F3A?VAM`^FheCS3KIsG%ER}5Uo"
    "zKyD*VUaZ}o%Wj0b?*eoTkVm1!`F+2!~B;)anO*8^_~q$`LG15P&Z#zsHDKh}t$c9;@Bn(GLVG9<-r&V|0ZT;!pbti>3gg*#"
    "jR{(Le!HUDoj8o){ERCbY*!`CVb)U=LZ?-t@Nx9YN>-SAoj3NIg6Kc?{nHKKD+e#j0GQi&v{)OB*4o9!`i{Cq@~H=mpcJZwF"
    "&YX->IOtvOp*G*Zc*b#CjjmWVU6-R6UA`;;<yhm^_;fiBMmdjITT9rz-pqB`82rEnoRQU{g5X2T*ImYz<(p96HtOOViux06h"
    "e*eqBx4?lnGcG;JL$RuA=)WI9I99CPx!rbCU<oper}DA8R*W8YMU88S2Y2!g`n79mx<gtP3G(((4~n`M3;Q6mj<z62(tjzcK"
    "6zX7t0<f73Ba#$_I73DE_OSYaEGq;b*`Xq9AuPDC^y3V%>K1+rnFtY^;V_!&tVXb6<m+=)pinS&|K4SthLxrIwZ9}hZ$nCGH"
    "R~JEys}jEL1t!wy4o?Cb!SUTD%ydx3!&^{?=uB%+JQ+NvR||$7L7LoH={CZNk@i<o=PcfhV&-e3HBRWSwppGRfS%aZv&um%("
    "V*rJ1Tvu~C(;n1_V3fwl#j)*3m~*)yfJHUZJQYq?`Ly(@`qF?5WEr!Sv^v94`#8$DCd))%5_Krf&94AABusCV)N<$?CA2M=X"
    "?8Xk&GZ?sr}Kn12u6x)vMp{XOa;@px{I892>M)$Q|&HbHpgf@w4(bw9nD>QP*SQ_EfhNH8b`+wFW9f_AgR|W2KX=06(PK*(Q"
    "mJeDrP~zo~fvbtqos9&`Wb#FH5t4|2t%WH-7!UV8J`SgW4aAD`Fe@AD6hv_u?-YA{tXAB-y+^<uRS&9RIzNAE;i<9ruL>ROH"
    "32wpU9aFp#cC_|kj<hd{un^gDj>w$H9)SS40ebi3C8N%fC4kDs{Ld&jo<%gvCZGeE^a^&vZ-f9lPW|9<m=#W$GLYF1pbNPSs"
    "UtWsFl`??AW-Y5n_r1F^`8LJZX@|{sNzli~uU0B(GAA^Gp~~6Ei@-8n(WQl2Rsg6nFcMSm}0)=78wAwgq~-xz#5WyUBxK)d="
    "s#Vo4VLS|I-Ed?cnUE`eB=0zdTGf;BX}_@3~iHF1BN2a#YCG$4A(SCW_^Vj(Wf^4I~=9ohHg&EH_|h{ukm=YarT@*d>%4?R("
    "QRi)>#uh#<aCK)B{o$F`|n3C_xwe|;%-x+(RRA*J;!@svn*E7#p`<7Z^GlE35yOUo%6&S_|-o#sL6t)S_Sz!V0$}3jpUO&>E"
    "@`pacpH{d@>kJU7xFaPxl&TQ9%0Q}O7eZY=+OovESFgFL;znP<%$H3V-%zF#5z~--_hxEj0Lcn^y$oq#pb(kw6Ft<?8NpU9n"
    "i8Oy&7B$mhj7vx8;@%eBR_n0(nE=J!-W6cI;E#(B{0Fnz)-#L>(eLNcy5|br>Q}v5ZwEHJy=+Lo1>AFbT5pRb2G%X)5vuyEC"
    "9g@9fpR)Yw_uJj-onAW-ce%EM$OkOO+~^ng;)-D@cre=r>8wbkmyT&gllC5Rjidn}a^;L^szCKIZ0^<zgCXj`P3huh)m2zc0"
    "_iEtzZM-WM=KSX@kpcfN#pz)W-HKzQy<qf~J4g4*<_-@P#B^RTb-lO>XK{G;3lSUn1V?rN>`>4O?{Qh|(%1ON*L5=DD2s^R("
    "QRF98vo0hTVaMa0Fs~Q#hSgISF4wlL=gRa%f^MaXu_Cw&l^dPdBq_p#6Ms2{t-)YYtebxMVw&$sA%ugFy<ybIKCsDDX+<iV0"
    "!q}Fm63=<8)m=(5Yd4oTafW+o7%&*-*`l;Ai}2oMYf*&l@7#-hLH&U$G&-Bwg~6QhY2q}xTbpj&Z@KzXM^ScqT{to~iH|sQ6"
    "G)?b*dfCgH$e`|(mW;=>oh`~m|Fo-?x5-!2Xi{OKA1JEL14`;d=)cER<;Zq>Q=RVolJ<rkx~V!d=frrytjxt{i1&he%Dy{@R"
    "A0JsAi<t_}+*Ujl3QionX{Zu@+uAO_ADjr6g%^;zQLX9~_33YqBY+&v1sJrwo5}ez`EbYr1Xf%`v4K6z>e4sm-qMW6$oajPW"
    "Dj<}Z66bU%>-$&|~F66Y*Go15(V^n>$U*a-;pO>}-k;k9%1Ln|h7R*C(Et5T}V^@(WWbc{6m())UMnT3KIYB;Lc+M`hZI=v+"
    "ig)KkF29M@DldK|TcCp`EGp`ZzeikGI&mR`k@qqqiIUM`SLOmnu3TTbRLKltn>eXt|`s81Uu-uHo^&(PC7IF~qc&up2aDvgf"
    "$fU-J>C?^CsjTO&jw-|*`@7st;S+O`;jXca>+=IQ+dhs}>NLJd5T;_NEj@s`M7x)-$Pf;OqvAO<=nHPbz8$b*cfV#E?OF--V"
    "?X?{%J0we=`w1$&h%D2aTlS5oveK3DTOpg(#?~Z>Cp%lPnjRo;VIZq$-kAiO`DMlfiJ#AzMzOkbIX<9M+b3XX(nVu`LUjcqe"
    "(D!br&zJl!ig=01dx|@sU=`k&uPePBwv^X@rgiNa2H`Ms?bZ*tZ^M-Xu+GLr&v~ouZ03!V8=yXN`gSyFDP-w{V<BY|F@(@p@"
    "XZMoYXDD+L2pn3W%sQ+l;h<^fc^)K3ya>tdsrd*?#(hEoj)MPvKiO@Fa@I||}}1ppHd6BNA26)9ev-I*Lo^uULorw~D{V*2D"
    "5WYhu`QI2%H^{uYAyplVb8%SYZwrEn6;a%T6yRfaCxEkE`o@G2Ftr&ZP-@$%gxKiT)kouhI>%jZQ4DVrGIOkBI({POX)R~3>"
    ")AWDKRPAwDnl^CcUX_1q(Vr}?@x-~eCU%NcLxz=}N@;ud7XgNaQOtlLabN{cxt5q~)M++Q;tsj>-OQ#zzn`915p&JdsL7=ic"
    "pj@P6gied8?S$OPayU5gMKv|6Z`x`N{@zDB+ikX{k#MC6xvwU{UT=2YRrj4R^H)HG`Lj%4YCAu2~*)|ytVL?ve-DiF>uc)qS"
    "n*=4WJ<n<=L%e0c=8LgYzCldv&$RxCh*q%y&VK`1hp|hxhXGQJ7kCJZi4m?)v9LG?f&GTYXN9CW!v|9l3DQ72efnC|qU{jrP"
    "Bf?b>tJZ@A&m+m?TCxk_+mrXaTqt5O8OfIM>^3ojaE+ioN_OZ*fY2Z~A`Y#{SF&zxBfMcV68=KfO1pK|sD%zZKLFq>myS)~j"
    "^H>;T!%cewZ4`)x*g-^a~1Yc=g_A~-8Vr8dc+uvy$J#6I}rsE6px<%X8$gPqRX;&C&NxFQt`?s**e?|M<Aj^VLcteeN!Y(UD"
    "QJDqbp&cMD;C@V4wVXPfc^Pu}4{VnM7ze@PbMuL+L4b~zU`x_Ce*`1XM=JjqSu|~Dz`{EK(Od5Zog?1(#d0Hem*w&P3G~XDX"
    "Z0BXiFNFKAcQ@<bB{9`%Yox-nU9w~zH|EO=+P1kZ<rR>3V!&YqfhTZt2iquMhg7-&F8~ztdfk&3iu~m=xu@3nq34(m)&7wSx"
    "<sq0`3-O;irl<mW(7<SANYclhFidnoTOn7cWLBoShX4(26>Du>mA4{`g{Ge9J-%!1X(05we&%_bXYroyiXZJ#EC;%RkF_@+R"
    "EE%|eLLavdtqcu&L?i({T&Rf7lc5qe31O~!n{%IcQPCl)}#UfPtF%Y~ORHd|~?`6+E|2b=pp<Q&u#-4_-4JkX5$TcMpH2qC9"
    "??;q^{0le+T9IJf-%TU)#qf5a9tK_1XCI;i}=~Z9exFo+PC|q8siO=Y!TKlaE;oU!N{9vY82yZ<KGw6iBqtTCz_{#l#F4exS"
    "w-P%qX-TxDutPS6oKv8cIo#k56UN=Ed5O-|790}maO}Fv2G+k212F8aq@B(z;lyu$ui%Yn^7ti-HrQp(+ZTILk&_|?rV2QH<"
    "N@)a>5Fi6X{h3CVg)Pp#>PGIZTd_7jgiTqj=o(36_II7Sf9n|=o7m<++YSAr1klqAC-W<QC|Z_@B*2#)M3_SyzX_*JzRK2=p"
    "|H`y`Dqvd4RTc^25$B4~mqMX4@4su<L!X(E1YCq7W_7QD>B_+=s)ta#wrz9&ohs+CB6WoDzSIyoZeC^#wOEC7XIRnPp`Ft_H"
    "rOvt|8K#BnKoIdAn54yj^pl*A^IF#?6O!$&XY)}j=3sqAUMe3Kr~lN|6IP}~(-^S6SotELsE(G)7mhK?UZ*=d5d#P2>b>K!e"
    "aZP1>cs5Ih4a|K<Bu=|es5tj?FtZ9Z&p?NBx3;<*{XRXy!S7ng}Q2R-2vHQ;l=0QkhZ6OmnyM}Ugo9W?i^98-gK02orCf@Fr"
    "B`bT`FkUB4bkXG}R1;|aOB6P$0zrcxhqUuPpg#nG>Ig=zMKZ8e{V!3GJs+Nc8z~FpVi!9+q=;0_c^-W)HZ$wA{&h1LHDjVs^"
    "vpLCJlqB730hCK!~#r6!6Jav$(BR_oYsMlD7WKC>mOZ(AWk1cTDmmikfKCpQ8sMO{^S5UWMF)RVW64*-_EGg(8(x#+{}<4>P"
    "x!fQKQRso$orMY~hMtsL4lrnjAdR73$hraEPtZ1<Z}|Z=5mO8QOr<AzV1~G)`OfVKj-_WsV@51oj=}cau|)8DomXto=td@B-"
    "mKlD!5Ky)+8R05Qp#QaAqc#{&;<CPvw!+o1;ki%o>~q1A}RVv{T<K>WhvFJo$ozQJ@;rZ4t6O)Hv83^XR+nvu%-(NZ0>|H<B"
    "t1-gtn92nZ?Yc>?8nSv2H8&^wOHpGWx)c&2L(Q@eUgGa4e>XYi=qkBp7)KKD2?ou_~1K*<w?iUv4bUAZJMA5$Px}ER_Tx8Vr"
    "A<2H$qTIy5JViS98@4VG=(Ten@vWc`Xp3^0Kh+)8ou%Kt)5mg%paozoOz~_!^VwD!yg}=QivShp(P>{KQR-Hhpl(QZ9Z8?*c"
    "+Gm_*E@B~5&6Lg2Y{hG-!7z_XsrAR4LO72*7YE!Awdg=I_{lg4-PY!6I1^Lm0~^G?5)dWFIJv$XFqy~4q>9YCu5R*!)#CXF*"
    "b<{@WY0o{k#f8E|oVNX9moofn(?x9895aR~|P%Fgg#*Q{r5QfNahxnX{72%C?mEPM*eGsKwb%7L`@0+<fK`+iMbzZU?25^CY"
    "bkSKTXc4O-7JtZ|`SoQ%4MYAjoADKGl?BQ)>!S3_@&Oa-P9ceHl0u|}twIMU0$EoZ~_O(ypa;ml%O3kCPr4q^ipDfGLw+;Hr"
    "WvckJ~)*C1UkwaEpH<ohhc7^e7aBl~!v^Fm>+j};aovR#xxFJH19;Wj;KB5%Mgt%7R_5=+~r729`QB{fM1Q9eED?jv+iR;V4"
    "ueqQt<F8ruRK3umxf_go9Nl-^zaMdzor6{ni*Z{XLGn5Dl{l~~;z;sJRjf8JpocE&ksJ2jKCNBQFYXEGCNjESp|B{ZY4@}%L"
    "K;@(pjQZ?*QBcswYxq`SMX<Ukv$w!AA82pR@jFcr>~;#G@CsMl%c)u#=q2A*mJu*uQ{S5!s5l&&0+<32J?nzmb2Cqlf{2fOp"
    "6i#G!VoEpm_uW+Ri(Le1ch{X(VxY;>*5XKQrTsej4e$i^snR`eyoOQoeI$E!a<@YwsR{I6!zOZEW6f$mvFNE%A*Nvv6+{#&p"
    "0ox$HQ5*oMWi-H^HZD?#evTv>z31(l?*9G)F{Fk*V>aWJCVD_d0FCHPwhVe0K}?<>6fRD4*@+%u0*u(+wj-Sqe)yc&X7Q1t>"
    "H(1}VzsEJAh$zHhX_xOgwEw3ZK>`d>emb7Ex83}lqC_Q-T8J0V}tmnAk0{*Dh^?UMMm|)!>>gz(MCoGSv-bebn<_wUNjKy^j"
    "bU`N(|MK90GWrs!M|q=(fzycB|5?BToZ)Kh2`B%=0E{J4(IX^rJX)}y8^pm#U7={Zqf=<ZFY!}$M%!>*nj&9<4>KBPq5q2X@"
    "7hgP4I49j^{<@ns~J*8Gg<rx8qKy0;c)5ipmnbAsL}clBNGE0)@q^*C2Acltlp-U9c9TBfWG?A<h;iyjV*PkW0vC8<dj~Ru7"
    "c?1w~A{pCk86!H(uzyQhh$fiv^wHzxMx10(A?qX(F?<6~>&~4!<$pkC6h6VEXE_l3)|Y41td<YR!XAq0+Z>j#hhKfv^rU0M)"
    "OUM9aN76k;V`sE}kTfrE*ajfrXJ%|5$Q-5=j8Xj(I+%pJEbUG|~}(LZ9Zf1<%LWx8{a8UX;`0p(;XaPtinpd&&1(*S<rxw=z"
    "J9okpHHXu|u<cQm#2qbBWWg{;Rwp;td#3zZ_i1amK0KP&=s4>3gs@UMwoxS|lyO~sOuvaQIA4Q>r?Rz6uxXO_ViRnCN5g~0<"
    "6b?x8Ak4%aO?~#^b*vIP1z3zs1KI-|8uNy#PK6ibA0*LCdOj%<hexPfLUFkpxvxE7P)QhK|Bf!LsdySGj5qYU6LQo?=^U1+Y"
    "D^p!Y68Xynj?I)I$ruFkZYXS9V95t0TepJC5qaCns7}qz*U@Q^qgDXmxD67qmo{F$cc*X+~$>d!gG@u#iA-^p1yA7MXqlYvI"
    "F7aNad5IzKJrtz>E560{EEJV#4POnVi*~ORBKqKz-ow`uR(-LMgrq%4z^2qJ!*zZ>`$)3Mx4dYn;KqsOQ`RvScELhdbf7;Xe"
    "$DLqkKsYTiaNG#LPG6qzN|1!f2@w3slUk?b68-F)BLZ3YB+&6-}InQL!HRimSbo}=_3pxSX;b20%;=!YGN1daG+05DXLf9CM"
    "uXXWC|(l(YX*j=wNn4H57>0vm2#FRr!a436xlQnlg`*ieGPZH<;c-eAEs;6AJQ$aDU4!bjOH9#rpChFIqroYqR=!|igNj=#-"
    "t=EMHOH>>tCRa*&!X_Jfpd4!^<gfN7!idw)*%f|lN&)|gLn7yP;Y>7=3Hbo_s~N7Xg7&)np91|hE!fRZE9si}5wY80j_!Klv"
    "sb`$KJH&$Aj}>4oMo^!x9BG9T+A1a{#y!0#_FD!M>>Q8Eb_t%h>_FbQC?9ydaea8-?gP?wml*|ExoAKW<^spn_7K(*6H|dS="
    "d|rCXc(ifCUfRmc}HFB(iZ@YGh8>y_H#^#2hi!a9*aB$EFiCRj3d~&ILa#g%kqG93w*-Uy6H|6BRxkS&V>dT0E1MwfGo9K7c"
    "Ouz!MGfqtyWXl0NWI<<zSwUBE>};Iuv=r90UX`zohI<I?r}ZZD&utC+b!D+R{Y=hEAAi&k<u08TWvd@yCau4DVq0*tHaD}gY"
    "K-tm=7-KeKE<xocCwV+Lh{87Zi#YrAdmr<pq1-qwI-(h1d{$e=^?f?%mSRxy&uwhwhTQiW2i!NbETBwsvXnOUX^g$~NDFUlp"
    "NIaoF)@Z4%1-Y+iIL_8~S;3#*AyhF4vV`VUZM1!Eso`y9q;^&NQ{hJ4qU{r=T3@=lg3Qkdxu0WppILZ+8+WL7>Ms}Dp&c~IS"
    "Gx_}qU^yp7|%OM6u0*iw$g2(Qxz~+g8#H_zNCj;Xz4gu_c2H8;zrn{sr?ND-t-cg{dZ)+FdSq>TYT&Fz^l|Y5Vf;E9S(@m&o"
    "GL2F)?5c9q9L`9(;fAR1ZM#Yf5bzy6ib!>z!28+6B?mt`B&?qs=B3gzR@8<8$CGp5I7fQl$`t@e%9We~4+-pMA07g7zTyH)B"
    "FANN4f$CtKnfh~NH^<H63{Y@8hqw0cH7OA%i3_~lGNeQmlpTDRUT1?Pjno)h4q4t!o)r5d0UuSp${<u329B0R?rS?x@?e5QL"
    "b1gN5E+m$^XduQa5CEcQs<J0p{gor2yGqEjstBu#CJ338W8sve)wWehpj&x`I>63UN)p(?yrFZZFuoJD3$dYVlszsxS5NucC"
    "zx{^bV6lD;a7*hhv#8&d+~<)x$^)cX(qAC1^#i%5O?L7xY7O7yvT29cPl4+evFZ46Nta{>g?$F9plYfQ`Ei$0BvV-Q`aaHLt"
    "HOKRL|MZ`U+&3KhDF-0%`3-_%7>JJm`dBNQWU#iKy+iAFcR6gQpB>yYNV)*4k^U~s<WPWE6g;+?G_s-&<H*`phoI<{kxR**}"
    "3cYzz*-c5LDuvDAO;(JI0(&@L|?%D)NiHW@(ESV#&)LI;04FL)c-dC-ME-tK{=^3TON1Bw-Kwv7CWC@C{)*BX9m{ch4~+kgd"
    "Bj;U>@7E!a*FyJ&{^y#Zt|%^C>=pmyV4QmmeDLu<*Bq@K81m<@;y7f!Vhs?4L1B-f+3-h@cbOO76)+iDxU$;inXILKXF3!~d"
    "W<v`gon!ppR36^Wg6}~JmqJD4%KHjS2r>msoL8Up-nL^bM<{22>33(-<3Go~!2cAU3-!WSu@D5=Z7;^9lZ9{uq*4Ys~TI(#7"
    "ZTw<VURP!%j^i;ZU79MEj={O#A-!1{cU}TQT>4YAd^Yi__Ol%>5B<UDK7Uq9Mx}WRX0f-eX~7H3=5H{NAB*kJ9a|oYEzn}vW"
    "*cfO=?-?RyD5oR;KMu>6<w&Wfrr_M?~b3qS+lQxIzuVA1M<-ey05TJB@*z@sx{lbQcl1^Y3#ps0j31?go7V4dqGvu1_fnsR@"
    "tUT<Uo+<ayG<9Fx{84wx~BsSjaX-4d}poUj&yy?<N2k?!8}T=7>Jpw0i_W_vVd>8zc(Krud^rr&_Dlj}G<$mXf|bTS@HA{Xy"
    "ulsEq&vQt?-ynTUT9t+C1-)49!+hA%?F0ljR+qCe*wz}Ju~n;>reILU-R!TYu=o`-oSL=;ju-UatZa0;!31so!A(+F5<b=ms"
    "mM}A;Yl>cnOK$$V^drSwrIZmD|mj|?SDF#JfZA~>Nw%K>1O?kvGupyI&=u&+gxiH$>^JH+}>~kep=)W~KY<x=nGD*{BiF?C$"
    "7fA5EkZ<*z+*3|g|0%Utg8Od&1WOPZMz;NXN54zN@;_5s`sK@|hEer5$6_~{$oWKSmBbjG*m@<=yHn6F<~!yH1#bM>ASO&EM"
    ";w>^b61dy`Ilkl{x-8^;K=O#{t}}?hX&zE%)ft=9`Ag0`?0d~QNCar;Mx;Rf?mS;OY)0abJ^RxllYGXRxmMkgD`zGpie<%E&"
    "pV9fte%~pXu|MGxwe%)^cv)_a7#`<3WDw!6)+poZG)j5<jzye|A{`9h#vuO!2^E!9^A0$Qoi0LPxy>uvv(a(mL!m1=RypS7b"
    "nXS3<yJe&0a7Hux0e_XrP~n3W!+j4rFio{*_9U2ZEiO@7A_(!z#8y+=bcAPINK=+fiyDZ{Xz3m%}fVO_hQIZ75Bq62bC2^ac"
    "(b@zabK<ktuvbDr&>8F3G)N5jyn$_Y?&M*WkYoRl%kb@34tx2>(Q#HT^y_hj>4WAx`COZoZSf}`WH)=Cmi`D_bm=gMi5Bisc"
    "?0VR+1hAo*oC77a<uw2gJc0$qvh69^BPrs&)}Tqf@m}^m6J>r#aO2lW;Ifv!X`o@DrPM4BS0wKcn{tPM<6-aDljy_QQp)kMm"
    "exm*IJv?Ihw`qT*jrt$KKX+Z9_{t;Y+(~X*9ZQX5WmH(CJGMp6q4E)1&i#2prd%9ksBC@uF9%WssEdmk+t6IZHT+3VxCMw3Y"
    "0z2))3+o`miBHliZ1xtl2-n-+Lr3%fZX*XvoA<@_&yO|K|jRMSbxnGXN%t_&7(|GF}k!!^1By8d4mTYm;))V`cwf+Hn13>><"
    "{Y5uiE@I*)0h<SGsNSloN$RSU1jvKAVK(Xc1Y?gX6H-3JcSATs%x8VJi}m8k<Zo!H5)_139@Yz~BuSo*$#YySH6IXMho=q1A"
    "ta^NBdTvj%Enmz<|Q+t+Pa0MT?4FMy$t<T*&PQ6KLCrH6EY)#5bO~1TzJ=gq5DI-1xkPFPM%7<7l)P`N}h<GabJ>{V>_CJ(p"
    "n=3VCtxRi?2)6|Jb0_gYdm8mJ@Xl}{ptd!#2~u5VF()EqJo_EVGEq;9a0TEi{a+}XT?U!=@jV3pn`m5!T6#o*fGJ|nbZauB<"
    "-YyY=kGw7J?KQ4sLDV(9Od^SD;|wl^xwH_DWZ~?{TB(%2W~<szIh+)f582hTHKYZaFf!Uk7i6W=Kq_2*|}3f%&$^uQt?_f!^"
    "8^U`Gn%n#Nxy9Ngiad!hzFwDv&3UA#&kh{iR-m6IKVlvhx2heXW}AJeU*G-zASDpu{aD)x#{owjfE@a88R8W<n4pYxT(3CDw"
    "{>6cJ;94`$(@yYJJin!>AfOL=Eq1?gv@{HTkgSChzm%XxZPJ(Y=*2qDr2>~6gH%#GRGx)^k2dU7%@jVV4vZn3)Po^OQf%vbr"
    "KEXr#ja1Ea9$#i@G3=#V*YEa7;H{JPr3Nt1sR%%@K>Mq--87$?TVWoFA0V}lOxNBr@0@Wx4sB|!CbuN&`nn5R9gGv$IWz|xo"
    "(yFK6fXqIoO*ccXcrKagBv26C?;Bqn0ZaeAm&#5b>iRv5Xr>o*RjInmmYHhRz+2UkK~fM^cM|NWrfsK8cFLM7gS^ev{^Siia"
    "Hny7vgbXPdtKG#lGDh$x6m@7t}Te+b)X4z{Bzrvh|{%l)na(ZQvq4NVTaVAlEyG}>AETIKpB&6#sqS|q{qzV<EHk2U*S}b?I"
    "W~LVy+bg!tlZ(u+sCH{8Q~=hME0Jk(~y*D%vx7yB6cXfCb22x?-YMGvq*0!2$6XJfUgub{jSOSnEp7CGHsm&S7i+rssa~ig&"
    "c0&%@IJJQ}`=Kcn+ay6SuMihf2N4@6?_EbuspsJ}ItW$yE{!bOq^C?O7(4S*V)BtgSZ_QHVdN`)kBN@Rsz@`#=~4ROOLfys>"
    "KqUV_a(E4E`Tx&Tt!Hr3tgC-o9cqo5IP8eA5TfpJ<+XV2NM6?DCRwm*=FWLCry3!ieE*lCO_9%?*?W88oU~dAZX9bxf1X$Ug"
    "E`>!BIX~g0aXQw=G~t^(Tz4p(>V*~`!80-cb&f&e(3dUSXO%!u|C2?IN|RsSrKW+*|CX9ZuogP*_`v-i4tM~ZRZq?-kTaoUn"
    "jFx}8F46p7BlPa+b)6(WCfqd2C}bXqq=wCvX+B4k$+64OgGBvA{z(`%5ZP$&o}XKR&vNtHn-+U+`hZ-TlZK$w}=ianY^)tzq"
    "=mMNQitRqU$Y4PJGq2bT40d3hp+x0#md--^O{!I<cRSKUf0(*@qnvC~HpyMYjbCZHJjmP9$))RNi~dp8}NdtiQ@Xi2%*iu9("
    "X~8P+;7CbVe%yq^Sv%|@Uks=Z_o^(vQJ1tEIm4(V{HBvh2_Pv!!bkhDw10~K|L1c>qz4T5*xWb~N^WhUQ=zIB==3W$gIOu~v"
    "V;K=>MEV<Sv?k-LfqxA$spa7Y*7`!ih?H;q95?+7PCXCI9>F_v{uXx0={W1>9;+v?WDyQ0Pcq1rgRB%W#?k;orAx#Tn(bX<@"
    "M0=M(go?r@b;9NW*S3$l7-R5yrk{Wz<xS0m9LGUN0^2ibCny8TNw0k59H5Yhp$ls)2N}U914X>uh(?6yLXS`>{bQL}neNx>7"
    "{kb4I0AVHv1#rE4~2njA_-VnKo`Ez@yDfVIZb@&w+JuSu=@iJcLh7h#sb-Xa&ZnE!@c7F7SDW)9jG7lYKXom<{xWK&A#Z<R1"
    "N-qkS3*D*&lZHM5-!I{~zLgo>E|d?W5F2-Z_lI4%8QlCN`-@MG;$28b#^Aky_;I5WGA~Lc#;XE0C(FQt-Kd`4lbkuJ!%OZW4"
    "KTQlnlWanw|+HB91V-eCbcn*l)BU5%xzJe#Qnm_T}E#PehjV{^r27<xM4pFg3H?c?+1-g}=%p_S6(mKX{9ZDn5RuBl%4wMms"
    "Q{l}?TjVmc;BS*T%;>^Z}Zi=K_#LEGg%@|Ta5*!bb$cUBvCMTQ4QzMlOMF~8(q_9?TTD>hikq3(D=9BD?;<7d&W(cgLi&B+="
    ";{leyM?s9jH^v;3ev0)8&OdQuG?<9OSZNhF+Wv=ylkKzwTj`tWcR#0E<!;!gYgZ<XA7(W>B<dReu$c%sMbdfiWQ7qcB;(NHV"
    "~F12Da}4}xv~R!T{i-?o1rt9*K5}BGLp2!%3EhStr7koffbmZnZNf}$BOQiG=sw-Ic~}uqQ5E6Eo7oH;HR1Ec31wm91kkJ1>"
    "`_Q=fcN{QziK&2675dv5sZ+emhcRt`UZVGE~o3%Ogt^5ak|Jh;uBcqt{c=cI>6yMt5IB?hg0a9h)8Buw^Ik>EdXW_f8G(c~J"
    "EgU<rRYv26~Mr_IOrC7iP3cw{5PasbE>dJ=twYAG7rS=|*k5JIC_enAW}oZ`CmR1PiL?5m2K2@8ji<gw=SuZH~1GZy9yO;v$"
    "3gooG<lCw1Y+fWNc|3h5P2TNh!s!Heq+Xm?RA!GyzV4@Lm1#^`+sN{a=$^~wtt*{wVa}Zd+K>Cu~9n$&KHC?CuTN3Q6YSehy"
    "BN)R<HK|O@fR@>{olaRMKVbre+-z`ontj6-KtH`o5`!E*ujkL=oNb%ZYEPB}ze5CLHrDRdO*=NRxhl?pl3kOLe(-L17zV*4V"
    "_A&sSUE>0!@L={3QI%!QNw%v^hXuD+;gubyR57jfp?uR(4-&gs$J$m4YK^P*A;R0g(ronD8853EA_8e?oL0Ud<d%QgY&l92-"
    "t)gFvMh~{Iv`xpf4=Tu1%Z?{<_eU4y{nnoyRenv&`K+1t}YX;g8V9Ld#jNx4DfZ$Qw1QWDKm+@PC4PsLx8#q7ux+L*m#}*lj"
    "Z-`~pY$v<d$#VS#G(PC7R-XbnAk*;o=*E_wmP9|R6_3Z*q^5anGlRRoTbY4>JBDT~9N@31ZX4aK%tK<7HuX!saNvm|EkH8EA"
    ")AonNCF@po23I3b3tA?H%g%bBz9^NSkLuq@ZVrdOF0^?#+<=qtIK4z9k)xmibu^rmNF&dC=P7{3?=dCXPW}wkbB{xZYlHfcM"
    "UYVx(xoBg8W)JAGb0~FnnxoK8qqJAAP;G_=!|f^U9V<zFg-OEcR#0KA^5Li&x*^~Aa=;B>DJO#Ta#ay`wAoNN<FMdGYR6U>U"
    "L~T(B3)K^Z`$ls5m8GPX5;jL1zdbmfHS9wS03*x+cd+@IG@6$AYOs0*S2I@ns5+$OdsdtdTdGaa<N{?{D@Y<=+5EX48#Q&YL"
    "|T!!T0;Pf#uJZ2bEATi)1f2NwKf^-1P;qo67VZOu&+~_Q23@bWzmvd!Bi~9l%rqodP9~Xy`1aGqv||4(EjxC`(;H>X@GL_Vg"
    "+$?TF}1pde%bxTprzLT@>{5Jwd70TvD3+?&4$$v~YXz?8#-3@A|CWRk}4uBaWs{RZkd?*k{nczbpDZR%yGl*-_XbL*8Oofu-"
    "}HQd??W_Ve~SrlOs=!{OGcP>aRF4gvTta1#SdHiWIDawS^*G!GJr&d4i8%YL(YD^r&;6X1526GDfVx)Rk?`MKt7G*5Jw+j3y"
    "+L+?tFBF`SVTW8i<||eKu}i+7I&%@aDrZh;&?LbVWBN>PO*g<yT>3<>R8n0GDx$yn$}25?y~gz*eTySHC^S3iOrGk)7UIWOK"
    "{hC5mpzWKwldyI$hs#6HRhlBD$rr@`N`qG5yx^4i-+f4@|!<PT4Y{jHk=)ixmaRlX|A(cC4M5vkS>Ife~*&xc85we-)zV=H)"
    "2syTl?Md?rgIEWvSk0rBxB@=4re56!37|wa!;v_yovz7aDu{Pc6=#ZXGtoINcb}I3O4)v*L2KiQsL%y7)a9$wt<%E7X!oNwP"
    "ENuJ~7Bf2`3p{O_Qaa*GQXNsbC8<5aP8L2S%wkB`Z%xA)WNPgrLM3h>JWVkRw-DoMM)YLB~Z_K~8~KG{_=r$a1aat?mShjn1"
    "v!>Fec0+kUX#@Wui#%`IH_ZqYQ*!`>U+c8w8aNV1B^@B98su7=Zv`Qj0^S$@A2a9V=i}+r81Ul?F4`h}l^YJ)Any5NYqabfn"
    "9WjF=$tnxW3a4L1OsE26MAue6Q(8R=R@xiDU~Z~hSL*}q<pF^9&?fCp39>_k$T`uZg15-$raopc_ASp!h$g*p(-YyGn<hV-w"
    "S}53ijWo-=vDIr7&rBOnm*MIrr3Q+pPv9;074T@qbJAWsb0@iCt24jSz<W!eNU>%6MKPD&zlTKQe~_x!d|a1Ahb-cd*{s)aJ"
    "DhMa>XT3y13g@%M7)AEM}pzzQAbFkmp_hu<^}59%RmJpTy!WfqnoGMC2$yHztG;G$F|E0?vO2;lN&gqxP%815k3lZ}fI^_XK"
    "Pe*L+qj!N1ccLQ^QT9=%2uqvxK){&UzdLgVplB}(ohhagJhyc^4tv`p5?sUU;Nu`rAhz7WHqI<)&*$X${Cw?jhfQQB4vxOe?"
    "p=)AW_h5@44f~<;-&dHAd3dYFwT%A4dV0ey|4P)}wKm;yE+$eC#LB9)`mW)x8RxW%TzRKA3lNvJ%@x1TbRdVhm(Q7$efN=fB"
    ")UT66ieCtzdG}cnN5KK3?vc@yeLpp-4u)t9rV?1=J8V;zKZ5{=dM_qMR-pzgX>2-B+>H$nn@$v$pt++{R=3fy5pKQR!}?Im6"
    ">;XN{>*n#_8)5TfN*7s92Ht`3efn%vBR?smggY)c{-ji>_JNCI0v>VFV=i=98Z!r6>TRB*7dBIBV-W`_Nhn>GvhH9`8d6n_J"
    "tse?)IJK5NYPKr)#+YeaHt+`h`{y+{XHs%ayE<X*eSQ@_@$uxDxu|Yqm0Zfe0}~UqFpUfp2r49(Hrl?34!3I^csYSUk=Q)*!"
    "U;WEC~W#LCjz=d0MKo;jJr9x)R6okJt~`*uhW1w>0c%iWRKyFY%w1}PqE+l$I779MN*aFCD*y|b*nnd|JfMAcfya>j}&uv6l"
    "+cC++UquS&39CB;<W*Arbp0pPBd2)BQ)Z?_t8Ieb1Nm<oH!8mh8Xq<0ld7~O?g{X&&rtjWyxP<?w!ILUof>K~50RRjbB6NM0"
    "B@|d>J<8uy#*q<789YM+b05?_CU|F$^0$Al!6LSS3d80mP<*D%Fo*hSCV&YgK9MSwumOqqHUqBc^D>5G3mD(hB1r>hFJ5nXe"
    "^3qO7!QA0v$A{1Wv7-X+<^E*r0@ufxaye3;oM^afsSTQDdAXd+#;157;l!f#&YX}mzgP^ed$Ww9j&%9yo)Jb))n5eVusZ?sP"
    "5Jc)X8c+K3B(G7C*zRQV{A`N#g;fouZ%U1R#DDN{F_Iau90><BR9Zt?)CU+L2IS5kF;!=ekD-hhD@cZ7vX#lNtGRB>7pKO@h"
    "Zml(a%Bg~^}6ZIR8X3M<9&4i0%$a{vO9!{g1ANdU0keNeC0)k|!VF4`YwiMP~LxN8?no2Y~Av>EP~8uLox)CcM+)f_;Ync6z"
    "QpkeZLOTyshyi8rH6$bhDX-<LRb0|!G6k1Pk#HZP@MVg?C5E`1e5re2=V143CyplA~syuuq;&0h^6a(o*4}a}}m3X&~J`4IM"
    "edWpq>}DM>ePa(tmKLh1pWoR5rl0<rSKFdi`;M&DnZrS)n_Z28v`b1#WDejJk@*2}FmC>*hc0svVrP*FeC5oDa%}A}hG`0lz"
    "L=PwoIO!pXDsUnmNBFo!{I5y3H+W{4v_A%&=+N^7-FoeA!9(miJ%HTjWA=`fp%8$ci<0inkn!<wk^vc{CjM(ivs?@;m{UunC"
    "(VStniT>v_W>#uFT2uIw(_wta_tZ3g&yRMxUzC$%e&xq&d6FWQLv2M{$+jzGpS)LStOP#GVwzAHcYQ4!V&cq2%!7x-N(t&fE"
    "_A;&X{G5BbSQKwq(NmO>|dCKjN4p~u#=j%HG4pB2GMS!6C$C<!Sy?gCgu{Vc6i!e07zGxtpqN`>BlGkm)^8r)vN`9C&#;BLS"
    ">Ye&pUUNRyq#*$3_Xi3|xE*l*~n2XvzmiTQ84d}rsf{4K9<8d97Ulz>iZP7@eMYDYGkZL7%emHDiYVd>6K>XZJmFbggLh+oe"
    "I(-mHO)^9xUjq6?Ys*sU4dgF-RAOE~K*W#6Nms?~1n{yhS8t-1&lq}l_?<h13c;qWwnBC?7cPDvp8!QPiF>WJt4C<@sC&U9m"
    "dL~ZRaJ*?aS?$I%jSkM6t%3aH;_-BZ^9?LpkmF~ug6JIN-)w=KB<_ohQp9&f|f-t4QW)c(c~QQm_}aT51@q<q;8li0Y78ewk"
    "whv*>sff>f1~VXJI_T;E#%s6qL3r1q8Kvy!^sN4l`e3l+i||2teuk`v#y1`(PuRBfV|?VG0i7@AUFtO%(S|xu2w&9j_0Gs}l"
    "GyExcQle`-4?hz1=qo-Xe=)n+bB?fPU+@qzTv<HHh4UJ|_#n!8~gY^S1PS%7HXllAs4V)GXJAa}kYa?lU8^mZ+xT=g)^(i-v"
    "B79LwwiP)dvB_#cR|3NO|VX5KS#SS1^t~{tShL1tElJ<!LhX(Hi;6}$hBxM|ve_WT5Pq>FxxGETS=bM8$IEtZIr1(!<yCkC^"
    "CIp7_eCFz&4Vow+$$^|x)6`gusaNr}Q^#Fi{}X~0FhVx;*tHs>i$4VxofFg5n-Bg+C1EnA2RX32q(&F2`Y-?H?0ib}2Mf`+u"
    "ZK~H4{c+@*L1eLxP<}kHg5Ep=gqoEA{}xZ$uOx~H((QvelPh^#*EptRdL}kR_~Cb@JU|_N?QdWo4WBTxnH=lpJ8i@0Na|0Ol"
    "|y{GsIiw_0-^~w)IjaLrj6FJ<uNLCA*tF_fUU#xs68`CP5(oDx(PLdzb~xeLyVAPlk-OXVw_sWXf<}x&(m#{Vy0XoGT0F!F9"
    "7)h|XORS+BK`M5>0YRwkmkM!3iHIW<L#r!<mL2n$FE<w(weAUCM*_;9EWSG>5r3!+`|Ubdw!9~?o<SXWs^g+g4R`>N8ZXnLs"
    "R?4n>3F}EjZUX96%@1qy$@#3|z^CNPv^&NWblwlsC+_sfNdDzR3kdY!zcKsRWr1J?b^yu?=m@dGC;v|a)V)fnc6E8;wuIU}W"
    "^ZN0z04X@33Z5?0t#l2VRghXxuH4<Lu$C&KKL;-T(3^Rw(c|krU}oh!+~TTK<X_L8t=r=AWvvmfi7K}`OJGEK3ri2XVtIR0P"
    "M*BKU$gESW~gkK`MtNiiR|xV@d5@*s&(r497N_{f{A-5QWnY=#$^`|B(gVjI`6P?i3)u4kv4O+K|gWVD1I&O3NlbV4cM#hLQ"
    "JqFd@Vhz&cd=0(O4`cS4pEj$Zf@`rW^_K*lnpFi|6>vUvghqNyb|Pt%|-S2x5088WdreN8zcOk=zAmuAIk`q0s(~@if|7lUZ"
    "A-jBlHUdT|te$IaS#R_0Jrm&9xj(-eAvr(?Z-;Y@&DoX?%iIFe}S>%KxMB04}A#p*W0Zr069t#9fF3prHA90P-&b7N>X3<gI"
    "C)8K|*|C&WFKnz=GA^HLD3E<8loZRB4dfDyhtIN@^P!33y>!JDI1$d83e;vPv4d`=mlf(}lHs{J#(h!bzcvAd%V_F;KW2*sH"
    "EN;@#n<oup)g>r9aupjb;|I^G{#kU#s;drMivM!K{(ryT2!1zCNlG#v$gG#47e|TX4zNkQ8G<xaXswhc+vvQ_S;NqO*UK->d"
    "FTjw0!{;{hF=*tjhdy@bfSsgTZJhan1r?0;2Ckklp1;=ar7Q?r~5HFUP85Z5j;P(M~vg+B7hy`-ng>3)*B#XYGo=wM%JW1xv"
    ")_THxjTzKYtYbv0m+{@~VLVi>IeRec6#W*T(2#_$d(}0%!56xE02(#;d_bREsiHJhXz=9^}K&$3#}}q1Wa8eiiZMbWT^v5FR"
    "&?pDmsh+Bl$&8d&rep|;n+u9)@BSE}1qJEqYX(??`<r~dm2JYo3&nEJch?p^)ahUc$hpobPj1LY#tmJ#1sEM(6EK?Ss($hSu"
    "%aU*8q5xdm21O=~9kr#hG+)BIMj%(wc*kwt1GLKcUTC#MX(SeEd)k2<*sjJc#cs+DU`p=il(@s2r=diEcu$XZLa9TxSXiox="
    "3D;Es+`++@d(eQT!*iY@zcsNI=I2+jF+awIG)+qgq^UlZ4|s0{2@l;m^gH$i1gmE9W?AQ`kKR^Cj+k{mIV=NJ(8T+z!aZhYS"
    "^>!3{sElCUt~W@C{?gRZRp?tz&u3OOYy^I&^DVm;9b84g7srzkNcmbCQ;lBnX^RjMC^ZxDo|@vdus-lZgPU&A#OxVZ>E)QxZ"
    "xPQTfNF^ezECA-!<nxH3N*H<TMW3Y5G{&!^^9B!q^0yW8DCIyoI<g#t<{BuhS->^^RSx(19XK9SF$I98(SAmZMlj9VbXaKlB"
    "Nq|9NZb*cwfxk{D;%Ul6m>!3vW?Z&C<#aay9RK%Yww3c>iRYraX@x&jJr6$up%PW$<VGw7v-BD<D#|HIMCZP1+Sw$AbX5)n7"
    "WTF3}<ay*Z7)yS9L1Qix}s~L*x;=2N=N14X&P&qlU8Nn*NL?0~b21dylh^;vOoa^RLPK)kP{M=hPm>wgEERP5N6B+Lae^>#7"
    "QudAh{g5?c56Y+5T|d{CD3U*x%z;1aR&E~!w6#Exy!m7t#-@ubCV<BbOX!}Mu(863H<eiO#?G}<w3O7OBnMdUYm7zJY7q_#i"
    "F2S_P?9mh`D@LW_<)zUOiO8PidD$$?OR7X@{#m$*ajtl2WEnQCh@e}_4#Eef_%o_uG~Ts_R8(CTzSdLgdX@IZ~ae|sX+6Ao-"
    "A|$-D1c0iK8>a=`5gyiTEtl^rSRCyZEfqVC%R@>{miSZi5r&yaxL$F)>sP@ncjRSKqz%$RSM4mR4V>m}`M$E896v&2|Zs`V@"
    "#;n^<cNw`mrVftHtWj^|&1Xw$R)j$`WVEeAorP7Vu^xtHPLq>&`Tw!i}uwL_kG7l;e}CxqHAg6B(iOT;pYvjqM$=W&=qT4Jh"
    "Y!dmv1c^c_ukG1?QI-+w;tRLt#o4-+lvhhSX@f|w{=)Lq=!U>VAz{8q`&<~^f$qBlI>^WUyU0EGc@Y-c*Pr+#8ZU8ilZ7fLU"
    "do{xQ*T--`4)JdjQh%KLjI{(aM+!x$*3j`-<Hd35dfn+qqH;GVh2s8kr-?FW1l!&rwS?tD57QCJ%TzY9"
)


_OUTPUT_ROOT_KEYS = (
    "schema_version",
    "source_interchange_schema_version",
    "source_semantic_schema_version",
    "input_stream_classification",
    "input_stream_commitment_sha256",
    "input_provenance_authenticated",
    "source_law_verified",
    "external_seed_source_verified",
    "runtime_lock_authenticated",
    "request_instance_sha256_authenticated",
    "stable_trace_sha256_authenticated",
    "cp61_estimand_digest_is_inventory_reference_only",
    "cp61_estimand_semantics_realized",
    "production_attempt_validity_evaluated",
    "production_recomputation",
    "arithmetic_transform_only",
    "request_count",
    "total_input_bytes",
    "estimand_count",
    "ordered_interchange_record_sha256",
    "ordered_projection_sha256",
    "ordered_seed_ordinal_plan_seed_sha256",
    "ordered_request_instance_sha256",
    "ordered_stable_trace_sha256",
    "runtime_lock_sha256",
    "estimand_estimate_intervals",
)
_OUTPUT_ESTIMAND_KEYS = (
    "schema_version",
    "estimand_ordinal",
    "estimand_id",
    "cp61_estimand_record_sha256",
    "estimand_family",
    "row_ordinal",
    "fixture_id",
    "strategy",
    "budget",
    "observable_cell_label",
    "first_attempt_one_based",
    "feature_id",
    "feature_lower_bound",
    "feature_upper_bound",
    "denominator_mode",
    "denominator_count",
    "success_count",
    "exact_feature_sum",
    "estimate",
    "interval_method",
    "interval_state",
    "interval_lower",
    "interval_upper",
    "development_supplied_input_only",
    "input_provenance_authenticated",
    "arithmetic_transform_only",
    "record_sha256",
)
_STREAM_COMMITMENT_PREIMAGE_KEYS = (
    "request_count",
    "total_input_bytes",
    "ordered_interchange_record_sha256",
    "ordered_projection_sha256",
    "ordered_seed_ordinal_plan_seed_sha256",
    "ordered_request_instance_sha256",
    "ordered_stable_trace_sha256",
    "runtime_lock_sha256",
)


class CP72SuppliedDevelopmentOutputValidationQualificationError(RuntimeError):
    """Fail-closed CP72 error carrying a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_ALLOW_RECORD_CLASS_DEFINITION = True


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP72 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP72 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP72 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP72PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    v22_protocol_sha256: str
    v22_protocol_bytes: int
    v22_protocol_lf_count: int
    v22_manifest_sha256: str
    v22_manifest_bytes: int
    v22_manifest_lf_count: int
    cp71_source_sha256: str
    cp71_test_sha256: str
    cp71_bundle_record_sha256: str
    cp71_stream_contract_record_sha256: str
    cp71_output_contract_record_sha256: str
    cp71_qualification_record_sha256: str
    cp71_fixture_set_sha256: str
    cp71_fixture_output_canonical_json_bytes: Tuple[int, ...]
    cp71_fixture_output_canonical_json_sha256s: Tuple[str, ...]
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP72SuppliedDevelopmentOutputValidationContractV1(_SealedRecord):
    schema_version: str
    contract_id: str
    source_output_schema_version: str
    source_interchange_schema_version: str
    source_semantic_schema_version: str
    input_type: str
    canonical_json_profile: str
    exact_output_root_keys: Tuple[str, ...]
    exact_estimand_record_keys: Tuple[str, ...]
    exact_stream_commitment_preimage_keys: Tuple[str, ...]
    request_count: int
    seed_count: int
    row_count: int
    estimand_count: int
    observable_estimand_count: int
    rejection_first_attempt_estimand_count: int
    feature_estimand_count: int
    binomial_estimand_count: int
    exact_cp61_inventory_crosswalk_required: bool
    exact_estimand_order_required: bool
    record_digest_recomputed: bool
    ordered_estimand_digest_computed: bool
    output_body_digest_computed: bool
    stream_commitment_internal_preimage_recomputed: bool
    cross_record_arithmetic_validated: bool
    exact_cp_endpoint_boundaries_validated: bool
    feature_arithmetic_validated: bool
    input_stream_relation_verified: bool
    input_provenance_authenticated: bool
    source_law_verified: bool
    production_attempt_validity_evaluated: bool
    operational_coverage_claimed: bool
    primary_thresholds_present: bool
    decision_fields_present: bool
    production_evidence_accepted: bool
    maximum_output_bytes: int
    maximum_declared_total_input_bytes: int
    maximum_output_record_bytes: int
    maximum_canonical_depth: int
    maximum_canonical_nodes: int
    maximum_key_characters: int
    maximum_text_characters: int
    maximum_integer_decimal_digits: int
    maximum_fraction_decimal_digits: int
    maximum_integer_bits: int
    maximum_cp_endpoint_cache_count: int
    maximum_output_vector_cardinality: int
    ordered_cp61_inventory_crosswalk_digest_domain: str
    estimand_record_digest_domain: str
    ordered_estimand_digest_domain: str
    output_body_digest_domain: str
    stream_commitment_digest_domain: str
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP72SuppliedDevelopmentOutputValidationSummaryV1(_SealedRecord):
    schema_version: str
    source_output_schema_version: str
    request_count: int
    estimand_count: int
    observable_estimand_count: int
    rejection_first_attempt_estimand_count: int
    feature_estimand_count: int
    binomial_estimand_count: int
    declared_total_input_bytes: int
    declared_input_stream_commitment_sha256: str
    declared_ordered_interchange_record_sha256: str
    declared_ordered_projection_sha256: str
    declared_ordered_seed_ordinal_plan_seed_sha256: str
    declared_ordered_request_instance_sha256: str
    declared_ordered_stable_trace_sha256: str
    declared_runtime_lock_sha256: str
    stream_commitment_coherence_verified: bool
    ordered_cp61_inventory_crosswalk_sha256: str
    ordered_estimand_record_sha256s_sha256: str
    output_body_sha256: str
    output_canonical_json_bytes: int
    output_canonical_json_sha256: str
    canonical_json_verified: bool
    schema_verified: bool
    estimand_inventory_and_order_verified: bool
    record_digests_verified: bool
    cross_record_arithmetic_verified: bool
    exact_interval_arithmetic_verified: bool
    selected_counts_by_row: Tuple[int, ...]
    observable_row_sums: Tuple[int, ...]
    rejection_first_attempt_row_sums: Tuple[int, ...]
    feature_estimate_present_count: int
    feature_estimate_absent_count: int
    binomial_interval_count: int
    feature_interval_count: int
    computed_interval_count: int
    insufficient_selection_count: int
    distinct_binomial_success_count_count: int
    exact_endpoint_boundary_comparison_count: int
    input_stream_relation_verified: bool
    input_provenance_authenticated: bool
    source_law_verified: bool
    production_attempt_validity_evaluated: bool
    operational_prediction: bool
    power_review_present: bool
    primary_thresholds_present: bool
    decision_made: bool
    production_evidence: bool
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP72SuppliedDevelopmentOutputValidationQualificationV1(_SealedRecord):
    schema_version: str
    fixture_set_sha256: str
    fixture_ids: Tuple[str, ...]
    fixture_validation_summary_record_sha256s: Tuple[str, ...]
    fixture_output_canonical_json_bytes: Tuple[int, ...]
    fixture_output_canonical_json_sha256s: Tuple[str, ...]
    fixture_selected_counts_by_row: Tuple[Tuple[int, ...], ...]
    fixture_computed_interval_counts: Tuple[int, ...]
    fixture_insufficient_selection_counts: Tuple[int, ...]
    fixture_count: int
    module_owned_total_output_bytes: int
    module_owned_peak_input_payload_count: int
    module_owned_peak_parsed_output_count: int
    maximum_simultaneously_materialized_estimand_record_count: int
    module_owned_output_payload_or_body_cached: bool
    caller_output_retained_after_successful_return: bool
    sealed_summary_snapshot_retained_while_summary_live: bool
    module_direct_filesystem_read: bool
    module_direct_filesystem_write: bool
    module_direct_clock_read: bool
    module_direct_rng_used: bool
    module_direct_network_used: bool
    module_direct_subprocess_used: bool
    source_independent: bool
    stdlib_only: bool
    input_stream_relation_verified: bool
    provenance_authenticated: bool
    production_recomputation_performed: bool
    operational_prediction: bool
    power_review_present: bool
    primary_thresholds_present: bool
    decision_path_qualified: bool
    production_gate_13_state: str
    production_gate_14_state: str
    production_evidence_present_count: int
    runner_and_recomputation_blocker_closed: bool
    formal_test_28_closed: bool
    all_development_qualification_checks_passed: bool
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP72SuppliedDevelopmentOutputValidationQualificationBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    blocker_ledger_prerequisite_id: str
    blocker_ledger_prerequisite_state: str
    blocker_ledger_total_count: int
    blocker_ledger_satisfied_count: int
    blocker_ledger_missing_count: int
    predecessor_custody: CP72PredecessorCustodyV1
    validation_contract: CP72SuppliedDevelopmentOutputValidationContractV1
    qualification_fixture_ids: Tuple[str, ...]
    qualification_fixture_specifications: Tuple[str, ...]
    zero_argument_builder: bool
    builder_validates: bool
    qualification_runner_zero_argument: bool
    public_supplied_output_validator_exposed: bool
    public_caller_data_api_count: int
    public_parser_exposed: bool
    public_stream_reducer_exposed: bool
    public_raw_record_api_exposed: bool
    public_stable_trace_api_exposed: bool
    public_path_api_exposed: bool
    public_writer_api_exposed: bool
    public_primary_decision_threshold_api_exposed: bool
    public_decision_api_exposed: bool
    public_receipt_or_evidence_api_exposed: bool
    project_modules_imported: bool
    source_independent: bool
    stdlib_only: bool
    production_execution_authorized: bool
    production_recomputation_qualified: bool
    unconditional_operational_predictions_produced: bool
    power_review_present: bool
    primary_thresholds_present: bool
    confirmatory_custody_present: bool
    runner_and_recomputation_blocker_closed: bool
    unconditional_operational_predictions_blocker_closed: bool
    power_and_thresholds_blocker_closed: bool
    confirmatory_custody_blocker_closed: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str
    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_RECORD_DOMAINS = {
    CP72PredecessorCustodyV1: b"cp72-test28-predecessor-custody-v1",
    CP72SuppliedDevelopmentOutputValidationContractV1: (
        b"cp72-test28-supplied-development-output-validation-contract-v1"
    ),
    CP72SuppliedDevelopmentOutputValidationSummaryV1: (
        b"cp72-test28-supplied-development-output-validation-summary-v1"
    ),
    CP72SuppliedDevelopmentOutputValidationQualificationV1: (
        b"cp72-test28-supplied-development-output-validation-qualification-v1"
    ),
    CP72SuppliedDevelopmentOutputValidationQualificationBundleV1: (
        b"cp72-test28-supplied-development-output-validation-qualification-bundle-v1"
    ),
}
_NESTED_RECORD_FIELD_TYPES = {
    CP72SuppliedDevelopmentOutputValidationQualificationBundleV1: (
        ("predecessor_custody", CP72PredecessorCustodyV1),
        ("validation_contract", CP72SuppliedDevelopmentOutputValidationContractV1),
    )
}
_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS = cast(
    "weakref.WeakKeyDictionary[_SealedRecord, Tuple[bytes, object, Tuple[_SealedRecord, ...]]]",
    weakref.WeakKeyDictionary(),
)


def _fail(code: str, message: str) -> None:
    raise CP72SuppliedDevelopmentOutputValidationQualificationError(code, message)


def _plain_json_value(
    value: object,
    *,
    depth: int = 1,
    nodes: Optional[list[int]] = None,
    active: Optional[set[int]] = None,
) -> object:
    if nodes is None:
        nodes = [0]
    if active is None:
        active = set()
    nodes[0] += 1
    if nodes[0] > CP72_TEST28_MAXIMUM_CANONICAL_NODES:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "canonical graph exceeds its node cap")
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        if cast(int, value).bit_length() > CP72_TEST28_MAXIMUM_INTEGER_BITS:
            _fail("CP72_INPUT_RESOURCE_LIMIT", "canonical integer exceeds its bit cap")
        return value
    if type(value) is Fraction:
        fraction = cast(Fraction, value)
        if (
            max(fraction.numerator.bit_length(), fraction.denominator.bit_length())
            > CP72_TEST28_MAXIMUM_INTEGER_BITS
        ):
            _fail("CP72_INPUT_RESOURCE_LIMIT", "canonical fraction exceeds its bit cap")
        return {"$fraction": [str(fraction.numerator), str(fraction.denominator)]}
    if type(value) is str:
        if len(cast(str, value)) > CP72_TEST28_MAXIMUM_TEXT_CHARACTERS:
            _fail("CP72_INPUT_RESOURCE_LIMIT", "canonical text exceeds its cap")
        try:
            cast(str, value).encode("utf-8")
        except UnicodeEncodeError as exc:
            raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                "CP72_INPUT_ENCODING_INVALID", "canonical text contains a surrogate"
            ) from exc
        return value
    if depth > CP72_TEST28_MAXIMUM_CANONICAL_DEPTH:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "canonical graph exceeds its depth cap")
    exact_type = type(value)
    if exact_type not in (tuple, list, dict) and exact_type not in _RECORD_DOMAINS:
        raise TypeError("value has no CP72 canonical representation")
    identity = id(value)
    if identity in active:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "canonical graph is cyclic")
    active.add(identity)
    try:
        if exact_type in (tuple, list):
            return [
                _plain_json_value(item, depth=depth + 1, nodes=nodes, active=active)
                for item in cast(tuple, value)
            ]
        if exact_type is dict:
            result = {}
            for key, item in cast(dict, value).items():
                if type(key) is not str:
                    raise TypeError("CP72 canonical keys must be exact strings")
                if len(key) > CP72_TEST28_MAXIMUM_KEY_CHARACTERS:
                    _fail("CP72_INPUT_RESOURCE_LIMIT", "canonical key exceeds its cap")
                try:
                    key.encode("utf-8")
                except UnicodeEncodeError as exc:
                    raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                        "CP72_INPUT_ENCODING_INVALID",
                        "canonical key contains a surrogate",
                    ) from exc
                result[key] = _plain_json_value(
                    item, depth=depth + 1, nodes=nodes, active=active
                )
            return result
        return {
            item.name: _plain_json_value(
                getattr(value, item.name),
                depth=depth + 1,
                nodes=nodes,
                active=active,
            )
            for item in fields(exact_type)
        }
    finally:
        active.remove(identity)


def _plain_json_bytes(
    value: object, maximum: int = CP72_TEST28_MAXIMUM_OUTPUT_BYTES
) -> bytes:
    try:
        encoded = json.dumps(
            _plain_json_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except CP72SuppliedDevelopmentOutputValidationQualificationError:
        raise
    except (OverflowError, RecursionError, TypeError, ValueError) as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INPUT_RESOURCE_LIMIT", "canonical encoding failed closed"
        ) from exc
    if len(encoded) > maximum:
        _fail("CP72_INPUT_BYTE_LIMIT", "canonical bytes exceed their cap")
    return encoded


def _typed_shape(
    value: object,
    *,
    depth: int,
    nodes: list[int],
    active: set[int],
    nested_records: list[_SealedRecord],
) -> object:
    nodes[0] += 1
    if nodes[0] > CP72_TEST28_MAXIMUM_CANONICAL_NODES:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "typed graph exceeds its node cap")
    if value is None:
        return ("none",)
    if type(value) is bool:
        return ("bool", cast(bool, value))
    if type(value) is int:
        return ("int", cast(int, value))
    if type(value) is str:
        return ("str", cast(str, value))
    if type(value) is Fraction:
        fraction = cast(Fraction, value)
        return ("fraction", fraction.numerator, fraction.denominator)
    if depth > CP72_TEST28_MAXIMUM_CANONICAL_DEPTH:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "typed graph exceeds its depth cap")
    exact_type = type(value)
    if exact_type in _RECORD_DOMAINS:
        nested = cast(_SealedRecord, value)
        nested_records.append(nested)
        return ("sealed-record", exact_type.__name__)
    if exact_type not in (tuple, list, dict):
        raise TypeError("typed graph contains an unsupported exact type")
    identity = id(value)
    if identity in active:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "typed graph is cyclic")
    active.add(identity)
    try:
        if exact_type in (tuple, list):
            return (
                "tuple" if exact_type is tuple else "list",
                tuple(
                    _typed_shape(
                        item,
                        depth=depth + 1,
                        nodes=nodes,
                        active=active,
                        nested_records=nested_records,
                    )
                    for item in cast(tuple, value)
                ),
            )
        entries = []
        for key, item in cast(dict, value).items():
            if type(key) is not str:
                raise TypeError("typed mapping key must be an exact string")
            entries.append(
                (
                    key,
                    _typed_shape(
                        item,
                        depth=depth + 1,
                        nodes=nodes,
                        active=active,
                        nested_records=nested_records,
                    ),
                )
            )
        return ("dict", tuple(sorted(entries, key=lambda entry: entry[0])))
    finally:
        active.remove(identity)


def _typed_record_state(
    record: _SealedRecord,
) -> Tuple[object, Tuple[_SealedRecord, ...]]:
    nested_records: list[_SealedRecord] = []
    nodes = [1]
    shape = (
        "record-root",
        type(record).__name__,
        tuple(
            (
                item.name,
                _typed_shape(
                    getattr(record, item.name),
                    depth=2,
                    nodes=nodes,
                    active={id(record)},
                    nested_records=nested_records,
                ),
            )
            for item in fields(type(record))
        ),
    )
    return shape, tuple(nested_records)


def _validate_nested_record_field_types(record: _SealedRecord) -> None:
    for name, expected_type in _NESTED_RECORD_FIELD_TYPES.get(type(record), ()):
        if type(getattr(record, name)) is not expected_type:
            raise TypeError("nested sealed-record field has the wrong exact type")


def _record(cls: type, values: Mapping[str, object]) -> object:
    if cls not in _RECORD_DOMAINS:
        raise TypeError("unsupported CP72 record class")
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("CP72 sealed record field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    complete["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls] + b"\0" + _plain_json_bytes(complete)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _plain_json_bytes(result, _MAXIMUM_SEALED_RECORD_BYTES)
    typed_snapshot, nested_records = _typed_record_state(cast(_SealedRecord, result))
    _validate_nested_record_field_types(cast(_SealedRecord, result))
    for nested_record in nested_records:
        _require_issued_record(nested_record)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = (
            snapshot,
            typed_snapshot,
            nested_records,
        )
    return result


def _require_issued_record_inner(
    value: object, *, active: set[int], nodes: list[int]
) -> Tuple[_SealedRecord, bytes]:
    if type(value) not in _RECORD_DOMAINS:
        _fail("CP72_RECORD_TYPE_MISMATCH", "record has an unsupported exact type")
    record = cast(_SealedRecord, value)
    with _ISSUED_RECORD_LOCK:
        issued = _ISSUED_RECORD_SNAPSHOTS.get(record)
    if issued is None:
        _fail("CP72_RECORD_NOT_ISSUED", "record was not issued by CP72")
    identity = id(record)
    nodes[0] += 1
    if (
        nodes[0] > CP72_TEST28_MAXIMUM_CANONICAL_NODES
        or len(active) >= CP72_TEST28_MAXIMUM_CANONICAL_DEPTH
        or identity in active
    ):
        _fail("CP72_RECORD_TAMPERED", "issued-record graph is not bounded")
    active.add(identity)
    try:
        snapshot, typed_snapshot, issued_nested = issued
        try:
            current_typed, nested = _typed_record_state(record)
            _validate_nested_record_field_types(record)
        except MemoryError:
            raise
        except Exception as exc:
            raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                "CP72_RECORD_TAMPERED", "issued record has an invalid typed shape"
            ) from exc
        if (
            current_typed != typed_snapshot
            or len(nested) != len(issued_nested)
            or any(
                current is not original
                for current, original in zip(nested, issued_nested)
            )
        ):
            _fail("CP72_RECORD_TAMPERED", "issued record typed state was mutated")
        for child in nested:
            try:
                _require_issued_record_inner(child, active=active, nodes=nodes)
            except MemoryError:
                raise
            except CP72SuppliedDevelopmentOutputValidationQualificationError as exc:
                if exc.code == "CP72_RESOURCE_EXHAUSTED":
                    raise
                raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                    "CP72_RECORD_TAMPERED", "nested issued record failed validation"
                ) from exc
        try:
            current = _plain_json_bytes(record, _MAXIMUM_SEALED_RECORD_BYTES)
            body = {
                item.name: getattr(record, item.name) for item in fields(type(record))
            }
            supplied = body["record_sha256"]
            body["record_sha256"] = _ZERO_SHA256
            expected = hashlib.sha256(
                _RECORD_DOMAINS[type(record)] + b"\0" + _plain_json_bytes(body)
            ).hexdigest()
        except MemoryError:
            raise
        except Exception as exc:
            raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                "CP72_RECORD_TAMPERED", "issued record cannot be reserialized"
            ) from exc
        if not hmac.compare_digest(snapshot, current):
            _fail("CP72_RECORD_TAMPERED", "issued record bytes were mutated")
        if type(supplied) is not str or not hmac.compare_digest(
            cast(str, supplied), expected
        ):
            _fail("CP72_RECORD_TAMPERED", "issued record digest differs")
        return record, snapshot
    finally:
        active.remove(identity)


def _require_issued_record(value: object) -> Tuple[_SealedRecord, bytes]:
    try:
        return _require_issued_record_inner(value, active=set(), nodes=[0])
    except CP72SuppliedDevelopmentOutputValidationQualificationError:
        raise
    except MemoryError as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_RESOURCE_EXHAUSTED", "issued-record validation exhausted memory"
        ) from exc


def cp72_canonical_json_bytes(value: object) -> bytes:
    """Return canonical bytes for one unchanged CP72-issued record."""

    return _require_issued_record(value)[1]


def cp72_sha256(value: object) -> str:
    """Return the tagged public digest of one unchanged CP72-issued record."""

    record, snapshot = _require_issued_record(value)
    return hashlib.sha256(
        b"cp72-public-record-v1\0"
        + type(record).__name__.encode("ascii")
        + b"\0"
        + snapshot
    ).hexdigest()


_ROW_SHAPES = tuple(
    (fixture_id, strategy, budget)
    for fixture_id in ("T28-M1-Q", "T28-M2-Q")
    for strategy, budgets in (
        ("bounded-rejection", (1, 4, 16, 64)),
        ("fixed-budget-sir", (8, 32, 128, 512)),
    )
    for budget in budgets
)
_REJECTION_OBSERVABLE_CELLS = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_SIR_OBSERVABLE_CELLS = (
    "returned-sir-selected-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_BINOMIAL_INTERVAL_METHOD = (
    "clopper-pearson-exact-rational-certified-equivalent-outward-endpoint-"
    "on-2^-256-grid-n2048"
)
_FEATURE_INTERVAL_METHOD = "bounded-feature-fixed-range-halfwidth-clipped-to-bounds"


def _row_key(row_ordinal: int) -> str:
    fixture_id, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    return "row-%02d/%s/%s/budget-%d" % (
        row_ordinal,
        fixture_id,
        strategy,
        budget,
    )


def _feature_projections(
    fixture_id: str,
) -> Tuple[Tuple[int, str, Tuple[Fraction, ...]], ...]:
    if fixture_id == "T28-M1-Q":
        return ((1, "axis0", (Fraction(1, 1),)),)
    if fixture_id != "T28-M2-Q":
        raise AssertionError("CP72 feature fixture differs")
    return (
        (0, "axis0", (Fraction(1, 1),)),
        (1, "axis0", (Fraction(1, 1), Fraction(0, 1))),
        (1, "axis1", (Fraction(0, 1), Fraction(1, 1))),
        (1, "diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
        (1, "diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
    )


@lru_cache(maxsize=2)
def _feature_ids(fixture_id: str) -> Tuple[str, ...]:
    cap = 1 if fixture_id == "T28-M1-Q" else 2
    dimensions = (0, 1) if fixture_id == "T28-M1-Q" else (1, 2)
    projections = _feature_projections(fixture_id)
    result = ["count/eq/%d" % count for count in range(cap + 1)]
    result.extend("type/%d/occupancy" % index for index in range(len(dimensions)))
    for type_index, projection_id, _coefficients in projections:
        result.extend(
            (
                "coordinate/%d/%s/odd" % (type_index, projection_id),
                "coordinate/%d/%s/even" % (type_index, projection_id),
            )
        )
    if cap == 2:
        by_type = {
            type_index: tuple(item for item in projections if item[0] == type_index)
            for type_index in range(len(dimensions))
        }
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                result.append("pair-type/%d/%d" % (left_type, right_type))
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                for left_position, left in enumerate(by_type[left_type]):
                    for right_position, right in enumerate(by_type[right_type]):
                        if left_type == right_type and right_position < left_position:
                            continue
                        result.append(
                            "pair-projection/%d/%s/%d/%s"
                            % (left_type, left[1], right_type, right[1])
                        )
    expected = 6 if fixture_id == "T28-M1-Q" else 33
    if len(result) != expected:
        raise AssertionError("CP72 feature identifier inventory differs")
    return tuple(result)


def _feature_bounds(feature_id: str) -> Tuple[Fraction, Fraction]:
    lower = (
        Fraction(-1, 1)
        if feature_id.endswith("/odd") or feature_id.startswith("pair-projection/")
        else Fraction(0, 1)
    )
    return lower, Fraction(1, 1)


def _iter_estimand_specs() -> Iterator[dict]:
    ordinal = 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        cells = (
            _REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else _SIR_OBSERVABLE_CELLS
        )
        for cell in cells:
            yield {
                "estimand_ordinal": ordinal,
                "estimand_id": "cp61/observable/%s/%s" % (_row_key(row), cell),
                "estimand_family": "observable-cell",
                "row_ordinal": row,
                "fixture_id": fixture,
                "strategy": strategy,
                "budget": budget,
                "observable_cell_label": cell,
                "first_attempt_one_based": None,
                "feature_id": None,
                "feature_lower_bound": None,
                "feature_upper_bound": None,
                "denominator_mode": "all-2048-supplied-seed-ordinal-groups",
            }
            ordinal += 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        if strategy != "bounded-rejection":
            continue
        for attempt in range(1, budget + 1):
            yield {
                "estimand_ordinal": ordinal,
                "estimand_id": "cp61/rejection-first-attempt/%s/attempt-%d"
                % (_row_key(row), attempt),
                "estimand_family": "rejection-first-attempt",
                "row_ordinal": row,
                "fixture_id": fixture,
                "strategy": strategy,
                "budget": budget,
                "observable_cell_label": None,
                "first_attempt_one_based": attempt,
                "feature_id": None,
                "feature_lower_bound": None,
                "feature_upper_bound": None,
                "denominator_mode": "all-2048-supplied-seed-ordinal-groups",
            }
            ordinal += 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        for feature_id in _feature_ids(fixture):
            lower, upper = _feature_bounds(feature_id)
            yield {
                "estimand_ordinal": ordinal,
                "estimand_id": "cp61/selected-feature/%s/%s"
                % (_row_key(row), feature_id),
                "estimand_family": "selected-conditional-feature",
                "row_ordinal": row,
                "fixture_id": fixture,
                "strategy": strategy,
                "budget": budget,
                "observable_cell_label": None,
                "first_attempt_one_based": None,
                "feature_id": feature_id,
                "feature_lower_bound": lower,
                "feature_upper_bound": upper,
                "denominator_mode": "predeadline-selected-count-in-this-row",
            }
            ordinal += 1
    if ordinal != CP72_TEST28_ESTIMAND_COUNT + 1:
        raise AssertionError("CP72 estimand inventory count differs")


_ESTIMAND_SPECS = tuple(_iter_estimand_specs())
if (
    len(_ROW_SHAPES) != CP72_TEST28_ROW_COUNT
    or len(_ESTIMAND_SPECS) != CP72_TEST28_ESTIMAND_COUNT
    or CP72_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY != CP72_TEST28_ESTIMAND_COUNT
):
    raise AssertionError("CP72 frozen inventory cardinality differs")


class _DuplicateKeyError(ValueError):
    pass


class _FloatTokenError(ValueError):
    pass


def _scan_json_lexical(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    index = 0
    while index < len(text):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            index += 1
            continue
        if character in "[{":
            depth += 1
            if depth > CP72_TEST28_MAXIMUM_CANONICAL_DEPTH:
                _fail("CP72_INPUT_RESOURCE_LIMIT", "JSON exceeds the CP72 depth cap")
        elif character in "]}":
            depth -= 1
        elif character.isdigit():
            start = index
            while index < len(text) and text[index].isdigit():
                index += 1
            if index - start > CP72_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS:
                _fail(
                    "CP72_INPUT_RESOURCE_LIMIT",
                    "JSON numeric token exceeds the CP72 decimal-digit cap",
                )
            continue
        index += 1


def _object_pairs_no_duplicates(pairs: list[Tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError("duplicate JSON object key")
        result[key] = value
    return result


def _parse_json_int(token: str) -> int:
    digits = token[1:] if token.startswith("-") else token
    if len(digits) > CP72_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "JSON integer exceeds its digit cap")
    value = int(token)
    if value.bit_length() > CP72_TEST28_MAXIMUM_INTEGER_BITS:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "JSON integer exceeds its bit cap")
    return value


def _reject_json_float(_token: str) -> object:
    raise _FloatTokenError("floating-point JSON token is forbidden")


def _walk_decoded(value: object, *, depth: int, nodes: list[int]) -> None:
    nodes[0] += 1
    if nodes[0] > CP72_TEST28_MAXIMUM_CANONICAL_NODES:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "decoded JSON exceeds its node cap")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if cast(int, value).bit_length() > CP72_TEST28_MAXIMUM_INTEGER_BITS:
            _fail("CP72_INPUT_RESOURCE_LIMIT", "decoded integer exceeds its bit cap")
        return
    if type(value) is str:
        text = cast(str, value)
        if len(text) > CP72_TEST28_MAXIMUM_TEXT_CHARACTERS:
            _fail("CP72_INPUT_RESOURCE_LIMIT", "decoded text exceeds its cap")
        try:
            text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                "CP72_INPUT_ENCODING_INVALID", "decoded text contains a surrogate"
            ) from exc
        return
    if depth > CP72_TEST28_MAXIMUM_CANONICAL_DEPTH:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "decoded JSON exceeds its depth cap")
    if type(value) is list:
        for item in cast(list, value):
            _walk_decoded(item, depth=depth + 1, nodes=nodes)
        return
    if type(value) is dict:
        for key, item in cast(dict, value).items():
            if type(key) is not str:
                _fail("CP72_INPUT_JSON_INVALID", "decoded key is not a string")
            if len(key) > CP72_TEST28_MAXIMUM_KEY_CHARACTERS:
                _fail("CP72_INPUT_RESOURCE_LIMIT", "decoded key exceeds its cap")
            try:
                key.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                    "CP72_INPUT_ENCODING_INVALID", "decoded key contains a surrogate"
                ) from exc
            _walk_decoded(item, depth=depth + 1, nodes=nodes)
        return
    _fail("CP72_INPUT_JSON_INVALID", "decoded JSON contains an unsupported value")


def _decoded_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (OverflowError, RecursionError, TypeError, ValueError) as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INPUT_RESOURCE_LIMIT", "decoded JSON cannot be canonicalized"
        ) from exc


def _decode_canonical_output_bytes(payload: object) -> dict:
    if type(payload) is not bytes:
        _fail("CP72_INPUT_TYPE_MISMATCH", "payload must be exact built-in bytes")
    body = cast(bytes, payload)
    if not body or len(body) > CP72_TEST28_MAXIMUM_OUTPUT_BYTES:
        _fail("CP72_INPUT_BYTE_LIMIT", "payload is empty or exceeds the output cap")
    try:
        text = body.decode("ascii")
    except UnicodeDecodeError as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INPUT_ENCODING_INVALID", "payload is not exact ASCII"
        ) from exc
    _scan_json_lexical(text)
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_pairs_no_duplicates,
            parse_int=_parse_json_int,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_float,
        )
    except CP72SuppliedDevelopmentOutputValidationQualificationError:
        raise
    except MemoryError:
        raise
    except (
        UnicodeError,
        _DuplicateKeyError,
        _FloatTokenError,
        json.JSONDecodeError,
    ) as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INPUT_JSON_INVALID", "payload is not accepted JSON"
        ) from exc
    except (OverflowError, RecursionError, ValueError) as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INPUT_RESOURCE_LIMIT", "JSON decoding exceeded a resource bound"
        ) from exc
    _walk_decoded(value, depth=1, nodes=[0])
    if _decoded_json_bytes(value) != body:
        _fail("CP72_INPUT_CANONICAL_MISMATCH", "payload is not exact canonical JSON")
    if type(value) is not dict:
        _fail("CP72_INPUT_FIELD_TYPE_MISMATCH", "output root must be a mapping")
    return cast(dict, value)


def _has_exact_fields(value: Mapping[str, object], names: Tuple[str, ...]) -> bool:
    return len(value) == len(names) and set(value) == set(names)


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(cast(str, value)) == 64
        and all(character in "0123456789abcdef" for character in cast(str, value))
    )


def _fraction_from_tag(value: object) -> Fraction:
    if type(value) is not dict or not _has_exact_fields(
        cast(dict, value), ("$fraction",)
    ):
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "fraction tag differs")
    pair = cast(dict, value)["$fraction"]
    if type(pair) is not list or len(cast(list, pair)) != 2:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "fraction component pair differs")
    numerator_text, denominator_text = cast(list, pair)
    if type(numerator_text) is not str or type(denominator_text) is not str:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "fraction components are not strings")
    numerator_string = cast(str, numerator_text)
    denominator_string = cast(str, denominator_text)
    numerator_digits = (
        numerator_string[1:] if numerator_string.startswith("-") else numerator_string
    )
    if (
        len(numerator_digits) > CP72_TEST28_MAXIMUM_FRACTION_DECIMAL_DIGITS
        or len(denominator_string) > CP72_TEST28_MAXIMUM_FRACTION_DECIMAL_DIGITS
    ):
        _fail("CP72_INPUT_RESOURCE_LIMIT", "fraction decimal component exceeds its cap")
    if not (
        numerator_digits == "0"
        or (
            numerator_digits
            and numerator_digits[0] in "123456789"
            and numerator_digits.isdigit()
        )
    ) or (numerator_string.startswith("-") and numerator_digits == "0"):
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "fraction numerator grammar differs")
    if not (
        denominator_string
        and denominator_string[0] in "123456789"
        and denominator_string.isdigit()
    ):
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "fraction denominator grammar differs")
    try:
        numerator = int(numerator_string)
        denominator = int(denominator_string)
    except (ValueError, MemoryError):
        raise
    if (
        max(numerator.bit_length(), denominator.bit_length())
        > CP72_TEST28_MAXIMUM_INTEGER_BITS
    ):
        _fail("CP72_INPUT_RESOURCE_LIMIT", "fraction component exceeds its bit cap")
    fraction = Fraction(numerator, denominator)
    if fraction.numerator != numerator or fraction.denominator != denominator:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "fraction is not reduced")
    return fraction


def _optional_fraction(value: object) -> Optional[Fraction]:
    return None if value is None else _fraction_from_tag(value)


def _fraction_bits(value: Fraction) -> None:
    if (
        max(value.numerator.bit_length(), value.denominator.bit_length())
        > CP72_TEST28_MAXIMUM_INTEGER_BITS
    ):
        _fail("CP72_INPUT_RESOURCE_LIMIT", "derived fraction exceeds its bit cap")


def _stream_commitment(values: Mapping[str, object]) -> str:
    return hashlib.sha256(
        _CP71_STREAM_COMMITMENT_DOMAIN + b"\0" + _decoded_json_bytes(dict(values))
    ).hexdigest()


def _validate_root(value: dict) -> Tuple[list, dict]:
    if not _has_exact_fields(value, _OUTPUT_ROOT_KEYS):
        _fail("CP72_INPUT_FIELD_SET_MISMATCH", "output root field set differs")
    string_names = (
        "schema_version",
        "source_interchange_schema_version",
        "source_semantic_schema_version",
        "input_stream_classification",
        "input_stream_commitment_sha256",
        "ordered_interchange_record_sha256",
        "ordered_projection_sha256",
        "ordered_seed_ordinal_plan_seed_sha256",
        "ordered_request_instance_sha256",
        "ordered_stable_trace_sha256",
        "runtime_lock_sha256",
    )
    boolean_names = (
        "input_provenance_authenticated",
        "source_law_verified",
        "external_seed_source_verified",
        "runtime_lock_authenticated",
        "request_instance_sha256_authenticated",
        "stable_trace_sha256_authenticated",
        "cp61_estimand_digest_is_inventory_reference_only",
        "cp61_estimand_semantics_realized",
        "production_attempt_validity_evaluated",
        "production_recomputation",
        "arithmetic_transform_only",
    )
    integer_names = ("request_count", "total_input_bytes", "estimand_count")
    if (
        any(type(value[name]) is not str for name in string_names)
        or any(type(value[name]) is not bool for name in boolean_names)
        or any(type(value[name]) is not int for name in integer_names)
    ):
        _fail("CP72_INPUT_FIELD_TYPE_MISMATCH", "output root field type differs")
    if type(value["estimand_estimate_intervals"]) is not list:
        _fail("CP72_INPUT_FIELD_TYPE_MISMATCH", "estimand vector type differs")
    expected_literals = {
        "schema_version": _CP71_OUTPUT_SCHEMA_VERSION,
        "source_interchange_schema_version": _CP69_SCHEMA_VERSION,
        "source_semantic_schema_version": _CP63_SEMANTIC_SCHEMA_VERSION,
        "input_stream_classification": _CP71_INPUT_STREAM_CLASSIFICATION,
        "input_provenance_authenticated": False,
        "source_law_verified": False,
        "external_seed_source_verified": False,
        "runtime_lock_authenticated": False,
        "request_instance_sha256_authenticated": False,
        "stable_trace_sha256_authenticated": False,
        "cp61_estimand_digest_is_inventory_reference_only": True,
        "cp61_estimand_semantics_realized": False,
        "production_attempt_validity_evaluated": False,
        "production_recomputation": False,
        "arithmetic_transform_only": True,
        "request_count": CP72_TEST28_REQUEST_COUNT,
        "estimand_count": CP72_TEST28_ESTIMAND_COUNT,
    }
    if any(value[name] != expected for name, expected in expected_literals.items()):
        _fail("CP72_INPUT_SCHEMA_MISMATCH", "output root schema literal differs")
    digest_names = (
        "input_stream_commitment_sha256",
        "ordered_interchange_record_sha256",
        "ordered_projection_sha256",
        "ordered_seed_ordinal_plan_seed_sha256",
        "ordered_request_instance_sha256",
        "ordered_stable_trace_sha256",
        "runtime_lock_sha256",
    )
    if any(not _is_sha256(value[name]) for name in digest_names):
        _fail("CP72_INPUT_DIGEST_MISMATCH", "output root digest grammar differs")
    commitment_fields = {name: value[name] for name in _STREAM_COMMITMENT_PREIMAGE_KEYS}
    wanted_commitment = _stream_commitment(commitment_fields)
    if not hmac.compare_digest(
        cast(str, value["input_stream_commitment_sha256"]), wanted_commitment
    ):
        _fail("CP72_INPUT_COMMITMENT_MISMATCH", "stream commitment preimage differs")
    total_input_bytes = cast(int, value["total_input_bytes"])
    if not (
        CP72_TEST28_REQUEST_COUNT
        <= total_input_bytes
        <= CP72_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES
    ):
        _fail(
            "CP72_INPUT_INVENTORY_MISMATCH", "declared input byte count is impossible"
        )
    records = cast(list, value["estimand_estimate_intervals"])
    if len(records) > CP72_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "estimand vector exceeds its cap")
    if len(records) != CP72_TEST28_ESTIMAND_COUNT:
        _fail("CP72_INPUT_INVENTORY_MISMATCH", "estimand vector count differs")
    return records, commitment_fields


def _upper_tail_compare(success_count: int, probability_numerator: int) -> int:
    n = CP72_TEST28_SEED_COUNT
    k = success_count
    a = probability_numerator
    if k <= 0:
        return 1
    if k > n or a == 0:
        return -1
    if a == _CP_DENOMINATOR:
        return 1
    complement = _CP_DENOMINATOR - a
    term = comb(n, k) * a**k * complement ** (n - k)
    partial = term
    index = k
    while True:
        left = partial * _CP_TAIL_RECIPROCAL
        if left > _CP_COMMON_DENOMINATOR_POWER:
            return 1
        if index == n:
            return (left > _CP_COMMON_DENOMINATOR_POWER) - (
                left < _CP_COMMON_DENOMINATOR_POWER
            )
        ratio_numerator = (n - index) * a
        ratio_denominator = (index + 1) * complement
        if ratio_numerator < ratio_denominator:
            gap = ratio_denominator - ratio_numerator
            bounded_left = (
                partial * gap + term * ratio_numerator
            ) * _CP_TAIL_RECIPROCAL
            if bounded_left < _CP_COMMON_DENOMINATOR_POWER * gap:
                return -1
        term, remainder = divmod(term * ratio_numerator, ratio_denominator)
        if remainder:
            _fail(
                "CP72_INTERNAL_INVARIANT_FAILED",
                "exact binomial recurrence is not integral",
            )
        partial += term
        index += 1


def _grid_numerator(value: Fraction) -> int:
    if value < 0 or value > 1 or _CP_DENOMINATOR % value.denominator:
        _fail(
            "CP72_INPUT_INTERVAL_MISMATCH",
            "binomial endpoint is not on the exact 2^-256 grid",
        )
    result = value.numerator * (_CP_DENOMINATOR // value.denominator)
    if not 0 <= result <= _CP_DENOMINATOR:
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "binomial endpoint is out of range")
    return result


def _certify_cp_interval(
    success: int,
    lower: Fraction,
    upper: Fraction,
    cache: dict[int, Tuple[Fraction, Fraction]],
    comparisons: list[int],
) -> None:
    if success in cache:
        if cache[success] != (lower, upper):
            _fail(
                "CP72_INPUT_INTERVAL_MISMATCH",
                "repeated success count has inconsistent endpoints",
            )
        return
    if len(cache) >= CP72_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "CP endpoint cache cap exceeded")
    lower_numerator = _grid_numerator(lower)
    upper_numerator = _grid_numerator(upper)
    if lower > upper:
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "binomial interval is reversed")
    if success == 0:
        if lower != 0:
            _fail("CP72_INPUT_INTERVAL_MISMATCH", "zero-success lower endpoint differs")
    else:
        if lower_numerator >= _CP_DENOMINATOR or not (
            _upper_tail_compare(success, lower_numerator) < 0
            and _upper_tail_compare(success, lower_numerator + 1) >= 0
        ):
            _fail(
                "CP72_INPUT_INTERVAL_MISMATCH",
                "lower endpoint lacks its adjacent exact witness",
            )
        comparisons[0] += 2
    if success == CP72_TEST28_SEED_COUNT:
        if upper != 1:
            _fail("CP72_INPUT_INTERVAL_MISMATCH", "all-success upper endpoint differs")
    else:
        complement_numerator = _CP_DENOMINATOR - upper_numerator
        complement_success = CP72_TEST28_SEED_COUNT - success
        if complement_numerator >= _CP_DENOMINATOR or not (
            _upper_tail_compare(complement_success, complement_numerator) < 0
            and _upper_tail_compare(complement_success, complement_numerator + 1) >= 0
        ):
            _fail(
                "CP72_INPUT_INTERVAL_MISMATCH",
                "upper endpoint lacks its adjacent exact witness",
            )
        comparisons[0] += 2
    cache[success] = (lower, upper)


def _validate_record_identity(record: dict, spec: Mapping[str, object]) -> None:
    if not _has_exact_fields(record, _OUTPUT_ESTIMAND_KEYS):
        _fail("CP72_INPUT_FIELD_SET_MISMATCH", "estimand field set differs")
    exact_string_names = (
        "schema_version",
        "estimand_id",
        "cp61_estimand_record_sha256",
        "estimand_family",
        "fixture_id",
        "strategy",
        "denominator_mode",
        "interval_method",
        "interval_state",
        "record_sha256",
    )
    exact_integer_names = (
        "estimand_ordinal",
        "row_ordinal",
        "budget",
        "denominator_count",
    )
    exact_boolean_names = (
        "development_supplied_input_only",
        "input_provenance_authenticated",
        "arithmetic_transform_only",
    )
    if (
        any(type(record[name]) is not str for name in exact_string_names)
        or any(type(record[name]) is not int for name in exact_integer_names)
        or any(type(record[name]) is not bool for name in exact_boolean_names)
    ):
        _fail("CP72_INPUT_FIELD_TYPE_MISMATCH", "estimand field type differs")
    nullable_identity_names = (
        "observable_cell_label",
        "first_attempt_one_based",
        "feature_id",
    )
    for name in nullable_identity_names:
        expected = spec[name]
        if expected is None:
            if record[name] is not None:
                _fail(
                    "CP72_INPUT_FIELD_TYPE_MISMATCH", "nullable identity field differs"
                )
        elif type(record[name]) is not type(expected):
            _fail("CP72_INPUT_FIELD_TYPE_MISMATCH", "identity field type differs")
    if spec["feature_lower_bound"] is None:
        if (
            record["feature_lower_bound"] is not None
            or record["feature_upper_bound"] is not None
        ):
            _fail(
                "CP72_INPUT_FIELD_TYPE_MISMATCH",
                "binomial feature bounds must be absent",
            )
    elif (
        type(record["feature_lower_bound"]) is not dict
        or type(record["feature_upper_bound"]) is not dict
    ):
        _fail("CP72_INPUT_FIELD_TYPE_MISMATCH", "feature bound type differs")
    else:
        for name in ("feature_lower_bound", "feature_upper_bound"):
            expected_fraction = cast(Fraction, spec[name])
            expected_tag = {
                "$fraction": [
                    str(expected_fraction.numerator),
                    str(expected_fraction.denominator),
                ]
            }
            if record[name] != expected_tag:
                _fail(
                    "CP72_INPUT_INVENTORY_MISMATCH",
                    "feature bound inventory differs",
                )
    for name in (
        "estimand_ordinal",
        "estimand_id",
        "estimand_family",
        "row_ordinal",
        "fixture_id",
        "strategy",
        "budget",
        "observable_cell_label",
        "first_attempt_one_based",
        "feature_id",
        "denominator_mode",
    ):
        if record[name] != spec[name]:
            _fail(
                "CP72_INPUT_INVENTORY_MISMATCH", "estimand inventory or order differs"
            )
    if record["schema_version"] != _CP71_OUTPUT_SCHEMA_VERSION:
        _fail("CP72_INPUT_SCHEMA_MISMATCH", "estimand schema differs")
    if not (
        record["development_supplied_input_only"] is True
        and record["input_provenance_authenticated"] is False
        and record["arithmetic_transform_only"] is True
    ):
        _fail("CP72_INPUT_SCHEMA_MISMATCH", "estimand claim literal differs")
    if not _is_sha256(record["cp61_estimand_record_sha256"]) or not _is_sha256(
        record["record_sha256"]
    ):
        _fail("CP72_INPUT_DIGEST_MISMATCH", "estimand digest grammar differs")


def _validate_record_digest(record: dict) -> bytes:
    encoded = _decoded_json_bytes(record)
    if len(encoded) > CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES:
        _fail("CP72_INPUT_RESOURCE_LIMIT", "estimand record byte cap exceeded")
    supplied = cast(str, record["record_sha256"])
    body = dict(record)
    body["record_sha256"] = _ZERO_SHA256
    wanted = hashlib.sha256(
        _CP71_ESTIMAND_RECORD_DOMAIN + b"\0" + _decoded_json_bytes(body)
    ).hexdigest()
    if not hmac.compare_digest(supplied, wanted):
        _fail("CP72_INPUT_DIGEST_MISMATCH", "estimand record digest differs")
    return bytes.fromhex(supplied)


def _validate_binomial_arithmetic(record: Mapping[str, object]) -> int:
    if type(record["success_count"]) is not int:
        _fail("CP72_INPUT_FIELD_TYPE_MISMATCH", "binomial success count type differs")
    success = cast(int, record["success_count"])
    if not 0 <= success <= CP72_TEST28_SEED_COUNT:
        _fail(
            "CP72_INPUT_ARITHMETIC_MISMATCH", "binomial success count is out of range"
        )
    if record["denominator_count"] != CP72_TEST28_SEED_COUNT:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "binomial denominator differs")
    if record["exact_feature_sum"] is not None:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "binomial exact sum must be absent")
    estimate = _optional_fraction(record["estimate"])
    if estimate is None:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "binomial estimate is absent")
    if estimate != Fraction(success, CP72_TEST28_SEED_COUNT):
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "binomial estimate differs")
    return success


def _validate_binomial_interval(
    record: Mapping[str, object],
    success: int,
    cache: dict[int, Tuple[Fraction, Fraction]],
    comparisons: list[int],
) -> None:
    if record["interval_method"] != _BINOMIAL_INTERVAL_METHOD:
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "binomial interval method differs")
    if record["interval_state"] != "computed":
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "binomial interval state differs")
    lower = _optional_fraction(record["interval_lower"])
    upper = _optional_fraction(record["interval_upper"])
    if lower is None or upper is None:
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "binomial endpoint is absent")
    _certify_cp_interval(success, lower, upper, cache, comparisons)


def _validate_feature_arithmetic(
    record: Mapping[str, object], spec: Mapping[str, object]
) -> int:
    if record["success_count"] is not None:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "feature success count must be absent")
    denominator = cast(int, record["denominator_count"])
    if not 0 <= denominator <= CP72_TEST28_SEED_COUNT:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "feature denominator is out of range")
    lower_bound = _optional_fraction(record["feature_lower_bound"])
    upper_bound = _optional_fraction(record["feature_upper_bound"])
    if (
        lower_bound != spec["feature_lower_bound"]
        or upper_bound != spec["feature_upper_bound"]
    ):
        _fail("CP72_INPUT_INVENTORY_MISMATCH", "feature bound inventory differs")
    if lower_bound is None or upper_bound is None or lower_bound >= upper_bound:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "feature bounds differ")
    total = _optional_fraction(record["exact_feature_sum"])
    estimate = _optional_fraction(record["estimate"])
    if denominator == 0:
        if total is not None or estimate is not None:
            _fail(
                "CP72_INPUT_ARITHMETIC_MISMATCH", "zero-selection feature value differs"
            )
        return denominator
    if total is None or estimate is None:
        _fail(
            "CP72_INPUT_ARITHMETIC_MISMATCH",
            "positive-selection feature value is absent",
        )
    if not lower_bound * denominator <= total <= upper_bound * denominator:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "feature sum exceeds its fixed bounds")
    wanted_estimate = total / denominator
    _fraction_bits(wanted_estimate)
    if estimate != wanted_estimate:
        _fail("CP72_INPUT_ARITHMETIC_MISMATCH", "feature estimate differs")
    return denominator


def _validate_feature_interval(
    record: Mapping[str, object], spec: Mapping[str, object], denominator: int
) -> bool:
    lower_bound = _optional_fraction(record["feature_lower_bound"])
    upper_bound = _optional_fraction(record["feature_upper_bound"])
    if lower_bound is None or upper_bound is None:
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "feature bounds are absent")
    if record["interval_method"] != _FEATURE_INTERVAL_METHOD:
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "feature interval method differs")
    total = _optional_fraction(record["exact_feature_sum"])
    estimate = _optional_fraction(record["estimate"])
    interval_lower = _optional_fraction(record["interval_lower"])
    interval_upper = _optional_fraction(record["interval_upper"])
    if denominator == 0:
        if (
            total is not None
            or estimate is not None
            or interval_lower is not None
            or interval_upper is not None
            or record["interval_state"] != "insufficient-selection"
        ):
            _fail(
                "CP72_INPUT_INTERVAL_MISMATCH", "zero-selection interval union differs"
            )
        return False
    if denominator < CP72_TEST28_MINIMUM_SELECTED_COUNT:
        if (
            record["interval_state"] != "insufficient-selection"
            or interval_lower is not None
            or interval_upper is not None
        ):
            _fail(
                "CP72_INPUT_INTERVAL_MISMATCH", "insufficient-selection union differs"
            )
        return False
    if total is None or estimate is None:
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "computed feature value is absent")
    halfwidth = (
        upper_bound - lower_bound
    ) * CP72_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER
    candidate_lower = estimate - halfwidth
    candidate_upper = estimate + halfwidth
    wanted_lower = max(lower_bound, candidate_lower)
    wanted_upper = min(upper_bound, candidate_upper)
    for fraction in (
        halfwidth,
        candidate_lower,
        candidate_upper,
        wanted_lower,
        wanted_upper,
    ):
        _fraction_bits(fraction)
    if (
        record["interval_state"] != "computed"
        or interval_lower != wanted_lower
        or interval_upper != wanted_upper
    ):
        _fail("CP72_INPUT_INTERVAL_MISMATCH", "feature interval arithmetic differs")
    return True


def _validate_output_value(value: dict, payload: bytes) -> dict:
    records, commitment_fields = _validate_root(value)
    ordered_records = hashlib.sha256(_CP71_ORDERED_ESTIMAND_DOMAIN + b"\0")
    ordered_cp61 = hashlib.sha256(_CP72_CP61_CROSSWALK_DOMAIN + b"\0")
    family_counts = {
        "observable-cell": 0,
        "rejection-first-attempt": 0,
        "selected-conditional-feature": 0,
    }
    for record, spec in zip(records, _ESTIMAND_SPECS):
        if type(record) is not dict:
            _fail("CP72_INPUT_FIELD_TYPE_MISMATCH", "estimand record is not a mapping")
        checked = cast(dict, record)
        _validate_record_identity(checked, spec)
        ordered_cp61.update(
            bytes.fromhex(cast(str, checked["cp61_estimand_record_sha256"]))
        )
        family_counts[cast(str, checked["estimand_family"])] += 1
    if family_counts != {
        "observable-cell": CP72_TEST28_OBSERVABLE_ESTIMAND_COUNT,
        "rejection-first-attempt": CP72_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
        "selected-conditional-feature": CP72_TEST28_FEATURE_ESTIMAND_COUNT,
    }:
        _fail("CP72_INPUT_INVENTORY_MISMATCH", "estimand family counts differ")
    cp61_digest = ordered_cp61.hexdigest()
    if not hmac.compare_digest(cp61_digest, _CP72_CP61_CROSSWALK_SHA256):
        _fail("CP72_INPUT_INVENTORY_MISMATCH", "CP61 inventory crosswalk differs")
    for record in records:
        ordered_records.update(_validate_record_digest(cast(dict, record)))

    observable_counts = {}
    attempt_counts = {}
    selected_counts: list[Optional[int]] = [None] * CP72_TEST28_ROW_COUNT
    feature_denominators: list[Optional[int]] = [None] * CP72_TEST28_ROW_COUNT
    feature_present = 0
    for record, spec in zip(records, _ESTIMAND_SPECS):
        checked = cast(dict, record)
        family = cast(str, checked["estimand_family"])
        row = cast(int, checked["row_ordinal"])
        if family == "observable-cell":
            success = _validate_binomial_arithmetic(checked)
            cell = cast(str, checked["observable_cell_label"])
            observable_counts[(row, cell)] = success
            selected_label = (
                _REJECTION_OBSERVABLE_CELLS[0]
                if checked["strategy"] == "bounded-rejection"
                else _SIR_OBSERVABLE_CELLS[0]
            )
            if cell == selected_label:
                selected_counts[row - 1] = success
        elif family == "rejection-first-attempt":
            success = _validate_binomial_arithmetic(checked)
            attempt_counts[
                (row, cast(int, checked["first_attempt_one_based"]))
            ] = success
        else:
            denominator = _validate_feature_arithmetic(checked, spec)
            previous = feature_denominators[row - 1]
            if previous is not None and previous != denominator:
                _fail(
                    "CP72_INPUT_ARITHMETIC_MISMATCH",
                    "feature denominators disagree within a row",
                )
            feature_denominators[row - 1] = denominator
            if checked["estimate"] is not None:
                feature_present += 1
    if any(value is None for value in selected_counts) or any(
        value is None for value in feature_denominators
    ):
        _fail(
            "CP72_INPUT_ARITHMETIC_MISMATCH", "selected-count inventory is incomplete"
        )
    selected_tuple = cast(Tuple[int, ...], tuple(selected_counts))
    if tuple(feature_denominators) != selected_tuple:
        _fail(
            "CP72_INPUT_ARITHMETIC_MISMATCH",
            "feature denominators differ from selection",
        )
    observable_row_sums = []
    rejection_first_sums = []
    for row, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        cells = (
            _REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else _SIR_OBSERVABLE_CELLS
        )
        row_sum = sum(observable_counts[(row, cell)] for cell in cells)
        observable_row_sums.append(row_sum)
        if row_sum != CP72_TEST28_SEED_COUNT:
            _fail(
                "CP72_INPUT_ARITHMETIC_MISMATCH", "observable row does not sum to 2048"
            )
        if strategy == "bounded-rejection":
            first_sum = sum(
                attempt_counts[(row, attempt)] for attempt in range(1, budget + 1)
            )
            rejection_first_sums.append(first_sum)
            if first_sum != selected_tuple[row - 1]:
                _fail(
                    "CP72_INPUT_ARITHMETIC_MISMATCH",
                    "rejection first-attempt counts differ from selection",
                )

    cp_cache: dict[int, Tuple[Fraction, Fraction]] = {}
    comparisons = [0]
    feature_intervals = 0
    for record, spec in zip(records, _ESTIMAND_SPECS):
        checked = cast(dict, record)
        family = cast(str, checked["estimand_family"])
        if family in ("observable-cell", "rejection-first-attempt"):
            _validate_binomial_interval(
                checked,
                cast(int, checked["success_count"]),
                cp_cache,
                comparisons,
            )
        elif _validate_feature_interval(
            checked, spec, cast(int, checked["denominator_count"])
        ):
            feature_intervals += 1
    return {
        **commitment_fields,
        "input_stream_commitment_sha256": value["input_stream_commitment_sha256"],
        "ordered_cp61_inventory_crosswalk_sha256": cp61_digest,
        "ordered_estimand_record_sha256s_sha256": ordered_records.hexdigest(),
        "output_body_sha256": hashlib.sha256(
            _CP71_OUTPUT_BODY_DOMAIN + b"\0" + payload
        ).hexdigest(),
        "output_canonical_json_bytes": len(payload),
        "output_canonical_json_sha256": hashlib.sha256(payload).hexdigest(),
        "selected_counts_by_row": selected_tuple,
        "observable_row_sums": tuple(observable_row_sums),
        "rejection_first_attempt_row_sums": tuple(rejection_first_sums),
        "feature_estimate_present_count": feature_present,
        "feature_estimate_absent_count": CP72_TEST28_FEATURE_ESTIMAND_COUNT
        - feature_present,
        "binomial_interval_count": CP72_TEST28_BINOMIAL_ESTIMAND_COUNT,
        "feature_interval_count": feature_intervals,
        "computed_interval_count": CP72_TEST28_BINOMIAL_ESTIMAND_COUNT
        + feature_intervals,
        "insufficient_selection_count": CP72_TEST28_FEATURE_ESTIMAND_COUNT
        - feature_intervals,
        "distinct_binomial_success_count_count": len(cp_cache),
        "exact_endpoint_boundary_comparison_count": comparisons[0],
    }


def cp72_validate_supplied_cp71_development_output_bytes(
    payload: object,
) -> CP72SuppliedDevelopmentOutputValidationSummaryV1:
    """Validate one bounded canonical CP71 development-output byte body."""

    try:
        value = _decode_canonical_output_bytes(payload)
        details = _validate_output_value(value, cast(bytes, payload))
        del value
        return cast(
            CP72SuppliedDevelopmentOutputValidationSummaryV1,
            _record(
                CP72SuppliedDevelopmentOutputValidationSummaryV1,
                {
                    "schema_version": CP72_TEST28_SCHEMA_VERSION,
                    "source_output_schema_version": _CP71_OUTPUT_SCHEMA_VERSION,
                    "request_count": CP72_TEST28_REQUEST_COUNT,
                    "estimand_count": CP72_TEST28_ESTIMAND_COUNT,
                    "observable_estimand_count": CP72_TEST28_OBSERVABLE_ESTIMAND_COUNT,
                    "rejection_first_attempt_estimand_count": CP72_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
                    "feature_estimand_count": CP72_TEST28_FEATURE_ESTIMAND_COUNT,
                    "binomial_estimand_count": CP72_TEST28_BINOMIAL_ESTIMAND_COUNT,
                    "declared_total_input_bytes": details["total_input_bytes"],
                    "declared_input_stream_commitment_sha256": details[
                        "input_stream_commitment_sha256"
                    ],
                    "declared_ordered_interchange_record_sha256": details[
                        "ordered_interchange_record_sha256"
                    ],
                    "declared_ordered_projection_sha256": details[
                        "ordered_projection_sha256"
                    ],
                    "declared_ordered_seed_ordinal_plan_seed_sha256": details[
                        "ordered_seed_ordinal_plan_seed_sha256"
                    ],
                    "declared_ordered_request_instance_sha256": details[
                        "ordered_request_instance_sha256"
                    ],
                    "declared_ordered_stable_trace_sha256": details[
                        "ordered_stable_trace_sha256"
                    ],
                    "declared_runtime_lock_sha256": details["runtime_lock_sha256"],
                    "stream_commitment_coherence_verified": True,
                    "ordered_cp61_inventory_crosswalk_sha256": details[
                        "ordered_cp61_inventory_crosswalk_sha256"
                    ],
                    "ordered_estimand_record_sha256s_sha256": details[
                        "ordered_estimand_record_sha256s_sha256"
                    ],
                    "output_body_sha256": details["output_body_sha256"],
                    "output_canonical_json_bytes": details[
                        "output_canonical_json_bytes"
                    ],
                    "output_canonical_json_sha256": details[
                        "output_canonical_json_sha256"
                    ],
                    "canonical_json_verified": True,
                    "schema_verified": True,
                    "estimand_inventory_and_order_verified": True,
                    "record_digests_verified": True,
                    "cross_record_arithmetic_verified": True,
                    "exact_interval_arithmetic_verified": True,
                    "selected_counts_by_row": details["selected_counts_by_row"],
                    "observable_row_sums": details["observable_row_sums"],
                    "rejection_first_attempt_row_sums": details[
                        "rejection_first_attempt_row_sums"
                    ],
                    "feature_estimate_present_count": details[
                        "feature_estimate_present_count"
                    ],
                    "feature_estimate_absent_count": details[
                        "feature_estimate_absent_count"
                    ],
                    "binomial_interval_count": details["binomial_interval_count"],
                    "feature_interval_count": details["feature_interval_count"],
                    "computed_interval_count": details["computed_interval_count"],
                    "insufficient_selection_count": details[
                        "insufficient_selection_count"
                    ],
                    "distinct_binomial_success_count_count": details[
                        "distinct_binomial_success_count_count"
                    ],
                    "exact_endpoint_boundary_comparison_count": details[
                        "exact_endpoint_boundary_comparison_count"
                    ],
                    "input_stream_relation_verified": False,
                    "input_provenance_authenticated": False,
                    "source_law_verified": False,
                    "production_attempt_validity_evaluated": False,
                    "operational_prediction": False,
                    "power_review_present": False,
                    "primary_thresholds_present": False,
                    "decision_made": False,
                    "production_evidence": False,
                },
            ),
        )
    except CP72SuppliedDevelopmentOutputValidationQualificationError:
        raise
    except MemoryError as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_RESOURCE_EXHAUSTED", "bounded output validation exhausted memory"
        ) from exc
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INTERNAL_INVARIANT_FAILED", "bounded output validation failed closed"
        ) from exc


def _predecessor_custody() -> CP72PredecessorCustodyV1:
    return cast(
        CP72PredecessorCustodyV1,
        _record(
            CP72PredecessorCustodyV1,
            {
                "schema_version": CP72_TEST28_SCHEMA_VERSION,
                "v22_protocol_sha256": _V22_PROTOCOL_SHA256,
                "v22_protocol_bytes": _V22_PROTOCOL_BYTES,
                "v22_protocol_lf_count": _V22_PROTOCOL_LF_COUNT,
                "v22_manifest_sha256": _V22_MANIFEST_SHA256,
                "v22_manifest_bytes": _V22_MANIFEST_BYTES,
                "v22_manifest_lf_count": _V22_MANIFEST_LF_COUNT,
                "cp71_source_sha256": _CP71_SOURCE_SHA256,
                "cp71_test_sha256": _CP71_TEST_SHA256,
                "cp71_bundle_record_sha256": _CP71_BUNDLE_RECORD_SHA256,
                "cp71_stream_contract_record_sha256": _CP71_STREAM_CONTRACT_RECORD_SHA256,
                "cp71_output_contract_record_sha256": _CP71_OUTPUT_CONTRACT_RECORD_SHA256,
                "cp71_qualification_record_sha256": _CP71_QUALIFICATION_RECORD_SHA256,
                "cp71_fixture_set_sha256": _CP71_FIXTURE_SET_SHA256,
                "cp71_fixture_output_canonical_json_bytes": _CP71_FIXTURE_OUTPUT_BYTES,
                "cp71_fixture_output_canonical_json_sha256s": _CP71_FIXTURE_OUTPUT_SHA256S,
            },
        ),
    )


def _validation_contract() -> CP72SuppliedDevelopmentOutputValidationContractV1:
    return cast(
        CP72SuppliedDevelopmentOutputValidationContractV1,
        _record(
            CP72SuppliedDevelopmentOutputValidationContractV1,
            {
                "schema_version": CP72_TEST28_SCHEMA_VERSION,
                "contract_id": "bounded-cp71-development-output-internal-validation-v1",
                "source_output_schema_version": _CP71_OUTPUT_SCHEMA_VERSION,
                "source_interchange_schema_version": _CP69_SCHEMA_VERSION,
                "source_semantic_schema_version": _CP63_SEMANTIC_SCHEMA_VERSION,
                "input_type": "exact-built-in-bytes",
                "canonical_json_profile": "ASCII-RFC8259-sort-keys-no-whitespace-no-float-no-duplicate-key-exact-bytes",
                "exact_output_root_keys": _OUTPUT_ROOT_KEYS,
                "exact_estimand_record_keys": _OUTPUT_ESTIMAND_KEYS,
                "exact_stream_commitment_preimage_keys": _STREAM_COMMITMENT_PREIMAGE_KEYS,
                "request_count": CP72_TEST28_REQUEST_COUNT,
                "seed_count": CP72_TEST28_SEED_COUNT,
                "row_count": CP72_TEST28_ROW_COUNT,
                "estimand_count": CP72_TEST28_ESTIMAND_COUNT,
                "observable_estimand_count": CP72_TEST28_OBSERVABLE_ESTIMAND_COUNT,
                "rejection_first_attempt_estimand_count": CP72_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
                "feature_estimand_count": CP72_TEST28_FEATURE_ESTIMAND_COUNT,
                "binomial_estimand_count": CP72_TEST28_BINOMIAL_ESTIMAND_COUNT,
                "exact_cp61_inventory_crosswalk_required": True,
                "exact_estimand_order_required": True,
                "record_digest_recomputed": True,
                "ordered_estimand_digest_computed": True,
                "output_body_digest_computed": True,
                "stream_commitment_internal_preimage_recomputed": True,
                "cross_record_arithmetic_validated": True,
                "exact_cp_endpoint_boundaries_validated": True,
                "feature_arithmetic_validated": True,
                "input_stream_relation_verified": False,
                "input_provenance_authenticated": False,
                "source_law_verified": False,
                "production_attempt_validity_evaluated": False,
                "operational_coverage_claimed": False,
                "primary_thresholds_present": False,
                "decision_fields_present": False,
                "production_evidence_accepted": False,
                "maximum_output_bytes": CP72_TEST28_MAXIMUM_OUTPUT_BYTES,
                "maximum_declared_total_input_bytes": CP72_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES,
                "maximum_output_record_bytes": CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES,
                "maximum_canonical_depth": CP72_TEST28_MAXIMUM_CANONICAL_DEPTH,
                "maximum_canonical_nodes": CP72_TEST28_MAXIMUM_CANONICAL_NODES,
                "maximum_key_characters": CP72_TEST28_MAXIMUM_KEY_CHARACTERS,
                "maximum_text_characters": CP72_TEST28_MAXIMUM_TEXT_CHARACTERS,
                "maximum_integer_decimal_digits": CP72_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS,
                "maximum_fraction_decimal_digits": CP72_TEST28_MAXIMUM_FRACTION_DECIMAL_DIGITS,
                "maximum_integer_bits": CP72_TEST28_MAXIMUM_INTEGER_BITS,
                "maximum_cp_endpoint_cache_count": CP72_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT,
                "maximum_output_vector_cardinality": CP72_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY,
                "ordered_cp61_inventory_crosswalk_digest_domain": _CP72_CP61_CROSSWALK_DOMAIN.decode(
                    "ascii"
                ),
                "estimand_record_digest_domain": _CP71_ESTIMAND_RECORD_DOMAIN.decode(
                    "ascii"
                ),
                "ordered_estimand_digest_domain": _CP71_ORDERED_ESTIMAND_DOMAIN.decode(
                    "ascii"
                ),
                "output_body_digest_domain": _CP71_OUTPUT_BODY_DOMAIN.decode("ascii"),
                "stream_commitment_digest_domain": _CP71_STREAM_COMMITMENT_DOMAIN.decode(
                    "ascii"
                ),
            },
        ),
    )


_QUALIFICATION_SELECTED_COUNTS = (
    (
        2_048,
        1_040,
        1_039,
        0,
        2_048,
        1_040,
        1_039,
        0,
        0,
        1_039,
        1_040,
        2_048,
        0,
        1_039,
        1_040,
        2_048,
    ),
    (2_048,) * CP72_TEST28_ROW_COUNT,
    (0,) * CP72_TEST28_ROW_COUNT,
    (1, 1_024, 2_047, 777) * 4,
    (
        2,
        17,
        257,
        513,
        769,
        1_038,
        1_041,
        1_283,
        1_537,
        1_793,
        2_046,
        3,
        511,
        778,
        1_023,
        2_045,
    ),
)
_QUALIFICATION_COMPUTED_INTERVAL_COUNTS = (398, 554, 242, 320, 386)
_QUALIFICATION_INSUFFICIENT_SELECTION_COUNTS = (156, 0, 312, 234, 168)
_QUALIFICATION_OUTPUT_BYTES = _CP71_FIXTURE_OUTPUT_BYTES + (696_156,)
_QUALIFICATION_OUTPUT_SHA256S = _CP71_FIXTURE_OUTPUT_SHA256S + (
    "8411f6657d0b689e1c6c7be3ff9f54fb2aeb0db19d166310574c4a3ec7ac2607",
)
_QUALIFICATION_FIXTURE_SET_DOMAIN = (
    b"cp72-test28-supplied-development-output-validation-qualification-fixture-set-v1"
)


def _qualification_decode_json(encoded: str) -> object:
    try:
        compressed = base64.b85decode(encoded.encode("ascii"))
        decoded = zlib.decompress(compressed)
        return json.loads(decoded.decode("ascii"))
    except MemoryError:
        raise
    except (UnicodeError, ValueError, TypeError, zlib.error) as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INTERNAL_INVARIANT_FAILED",
            "frozen qualification specification failed closed",
        ) from exc


def _qualification_cp61_record_sha256s() -> Tuple[str, ...]:
    try:
        raw = base64.b85decode(_CP61_ESTIMAND_RECORD_SHA256_B85.encode("ascii"))
    except MemoryError:
        raise
    except (ValueError, TypeError) as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INTERNAL_INVARIANT_FAILED",
            "frozen CP61 inventory failed closed",
        ) from exc
    if len(raw) != 32 * CP72_TEST28_ESTIMAND_COUNT:
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "CP61 digest inventory length differs")
    wanted = hashlib.sha256(_CP72_CP61_CROSSWALK_DOMAIN + b"\0" + raw).hexdigest()
    if not hmac.compare_digest(wanted, _CP72_CP61_CROSSWALK_SHA256):
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "CP61 digest inventory custody differs")
    return tuple(raw[offset : offset + 32].hex() for offset in range(0, len(raw), 32))


def _qualification_cp_endpoints() -> dict[int, Tuple[Fraction, Fraction]]:
    decoded = _qualification_decode_json(_QUALIFICATION_CP_ENDPOINTS_B85)
    if type(decoded) is not dict:
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "endpoint inventory type differs")
    result = {}
    for success_text, pair in cast(dict, decoded).items():
        if type(success_text) is not str or type(pair) is not list or len(pair) != 2:
            _fail("CP72_INTERNAL_INVARIANT_FAILED", "endpoint inventory shape differs")
        try:
            success = int(success_text)
            lower_pair, upper_pair = cast(list, pair)
            if (
                type(lower_pair) is not list
                or type(upper_pair) is not list
                or len(lower_pair) != 2
                or len(upper_pair) != 2
            ):
                raise ValueError("endpoint component shape differs")
            lower = Fraction(int(lower_pair[0]), int(lower_pair[1]))
            upper = Fraction(int(upper_pair[0]), int(upper_pair[1]))
        except MemoryError:
            raise
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                "CP72_INTERNAL_INVARIANT_FAILED",
                "endpoint inventory value failed closed",
            ) from exc
        if not 0 <= success <= CP72_TEST28_SEED_COUNT or not 0 <= lower <= upper <= 1:
            _fail("CP72_INTERNAL_INVARIANT_FAILED", "endpoint inventory value differs")
        result[success] = (lower, upper)
    return result


def _qualification_fraction_pair(value: object) -> Optional[Fraction]:
    if value is None:
        return None
    if type(value) is not list or len(cast(list, value)) != 2:
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture fraction pair differs")
    try:
        return Fraction(int(cast(list, value)[0]), int(cast(list, value)[1]))
    except MemoryError:
        raise
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise CP72SuppliedDevelopmentOutputValidationQualificationError(
            "CP72_INTERNAL_INVARIANT_FAILED",
            "fixture fraction failed closed",
        ) from exc


def _qualification_nonfixture_feature_sum(
    selected_count: int, feature_index: int, lower_bound: Fraction
) -> Fraction:
    period = 33 if lower_bound == -1 else 17
    offset = 16 if lower_bound == -1 else 0
    cycle_total = sum(
        (seed + feature_index) % period - offset for seed in range(1, period + 1)
    )
    cycles, remainder = divmod(selected_count, period)
    remainder_total = sum(
        (seed + feature_index) % period - offset for seed in range(1, remainder + 1)
    )
    return Fraction(cycles * cycle_total + remainder_total, 16)


def _qualification_nonfixture_specification() -> dict:
    selected = _QUALIFICATION_SELECTED_COUNTS[-1]
    binomial = []
    feature = []
    for spec in _ESTIMAND_SPECS:
        family = cast(str, spec["estimand_family"])
        row = cast(int, spec["row_ordinal"])
        selected_count = selected[row - 1]
        if family == "observable-cell":
            cells = (
                _REJECTION_OBSERVABLE_CELLS
                if spec["strategy"] == "bounded-rejection"
                else _SIR_OBSERVABLE_CELLS
            )
            cell = spec["observable_cell_label"]
            if cell == cells[0]:
                binomial.append(selected_count)
            elif cell == cells[1]:
                binomial.append(CP72_TEST28_SEED_COUNT - selected_count)
            else:
                binomial.append(0)
        elif family == "rejection-first-attempt":
            binomial.append(
                selected_count if spec["first_attempt_one_based"] == 1 else 0
            )
        else:
            feature_id = cast(str, spec["feature_id"])
            feature_index = _feature_ids(cast(str, spec["fixture_id"])).index(
                feature_id
            )
            total = _qualification_nonfixture_feature_sum(
                selected_count,
                feature_index,
                cast(Fraction, spec["feature_lower_bound"]),
            )
            feature.append([str(total.numerator), str(total.denominator)])
    root = {
        "schema_version": _CP71_OUTPUT_SCHEMA_VERSION,
        "source_interchange_schema_version": _CP69_SCHEMA_VERSION,
        "source_semantic_schema_version": _CP63_SEMANTIC_SCHEMA_VERSION,
        "input_stream_classification": _CP71_INPUT_STREAM_CLASSIFICATION,
        "input_provenance_authenticated": False,
        "source_law_verified": False,
        "external_seed_source_verified": False,
        "runtime_lock_authenticated": False,
        "request_instance_sha256_authenticated": False,
        "stable_trace_sha256_authenticated": False,
        "cp61_estimand_digest_is_inventory_reference_only": True,
        "cp61_estimand_semantics_realized": False,
        "production_attempt_validity_evaluated": False,
        "production_recomputation": False,
        "arithmetic_transform_only": True,
        "request_count": CP72_TEST28_REQUEST_COUNT,
        "total_input_bytes": 70_000_000,
        "estimand_count": CP72_TEST28_ESTIMAND_COUNT,
    }
    for name in (
        "ordered_interchange_record_sha256",
        "ordered_projection_sha256",
        "ordered_seed_ordinal_plan_seed_sha256",
        "ordered_request_instance_sha256",
        "ordered_stable_trace_sha256",
        "runtime_lock_sha256",
    ):
        root[name] = hashlib.sha256(
            b"cp72-test28-qualification-nonfixture-opaque-identity-v1\0"
            + name.encode("ascii")
        ).hexdigest()
    root["input_stream_commitment_sha256"] = _stream_commitment(
        {name: root[name] for name in _STREAM_COMMITMENT_PREIMAGE_KEYS}
    )
    return {"root": root, "binomial": binomial, "feature": feature}


def _qualification_fixture_specification(fixture_id: str) -> dict:
    if fixture_id == CP72_TEST28_QUALIFICATION_FIXTURE_IDS[-1]:
        result = _qualification_nonfixture_specification()
    else:
        encoded = _QUALIFICATION_AGGREGATE_SPECIFICATIONS_B85.get(fixture_id)
        if encoded is None:
            _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture identifier differs")
        result = _qualification_decode_json(encoded)
    if type(result) is not dict or set(cast(dict, result)) != {
        "root",
        "binomial",
        "feature",
    }:
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture specification shape differs")
    checked = cast(dict, result)
    if (
        type(checked["root"]) is not dict
        or type(checked["binomial"]) is not list
        or type(checked["feature"]) is not list
        or len(cast(list, checked["binomial"])) != CP72_TEST28_BINOMIAL_ESTIMAND_COUNT
        or len(cast(list, checked["feature"])) != CP72_TEST28_FEATURE_ESTIMAND_COUNT
    ):
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture aggregate inventory differs")
    return checked


def _qualification_estimand_record(
    spec: Mapping[str, object],
    cp61_sha256: str,
    success: Optional[int],
    selected_count: int,
    exact_feature_sum: Optional[Fraction],
    endpoints: Mapping[int, Tuple[Fraction, Fraction]],
) -> dict:
    family = cast(str, spec["estimand_family"])
    if family in ("observable-cell", "rejection-first-attempt"):
        if type(success) is not int or success not in endpoints:
            _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture success inventory differs")
        denominator = CP72_TEST28_SEED_COUNT
        total = None
        estimate = Fraction(cast(int, success), denominator)
        interval_lower, interval_upper = endpoints[cast(int, success)]
        interval_method = _BINOMIAL_INTERVAL_METHOD
        interval_state = "computed"
    else:
        success = None
        denominator = selected_count
        total = exact_feature_sum if denominator else None
        estimate = total / denominator if denominator and total is not None else None
        interval_method = _FEATURE_INTERVAL_METHOD
        if estimate is None or denominator < CP72_TEST28_MINIMUM_SELECTED_COUNT:
            interval_lower = interval_upper = None
            interval_state = "insufficient-selection"
        else:
            feature_lower = cast(Fraction, spec["feature_lower_bound"])
            feature_upper = cast(Fraction, spec["feature_upper_bound"])
            halfwidth = (
                feature_upper - feature_lower
            ) * CP72_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER
            interval_lower = max(feature_lower, estimate - halfwidth)
            interval_upper = min(feature_upper, estimate + halfwidth)
            interval_state = "computed"
    body = {
        "schema_version": _CP71_OUTPUT_SCHEMA_VERSION,
        **dict(spec),
        "cp61_estimand_record_sha256": cp61_sha256,
        "denominator_count": denominator,
        "success_count": success,
        "exact_feature_sum": total,
        "estimate": estimate,
        "interval_method": interval_method,
        "interval_state": interval_state,
        "interval_lower": interval_lower,
        "interval_upper": interval_upper,
        "development_supplied_input_only": True,
        "input_provenance_authenticated": False,
        "arithmetic_transform_only": True,
        "record_sha256": _ZERO_SHA256,
    }
    body["record_sha256"] = hashlib.sha256(
        _CP71_ESTIMAND_RECORD_DOMAIN + b"\0" + _plain_json_bytes(body)
    ).hexdigest()
    if len(_plain_json_bytes(body)) > CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES:
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture output record cap differs")
    return body


def _build_qualification_fixture_output(
    fixture_id: str,
    endpoints: Mapping[int, Tuple[Fraction, Fraction]],
    cp61_sha256s: Tuple[str, ...],
) -> bytes:
    data = _qualification_fixture_specification(fixture_id)
    root = cast(dict, data["root"])
    if not _has_exact_fields(
        root,
        tuple(
            name for name in _OUTPUT_ROOT_KEYS if name != "estimand_estimate_intervals"
        ),
    ):
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture root inventory differs")
    binomial_values = iter(cast(list, data["binomial"]))
    feature_values = iter(cast(list, data["feature"]))
    selected_by_row: list[Optional[int]] = [None] * CP72_TEST28_ROW_COUNT
    binomial_by_ordinal = {}
    for spec in _ESTIMAND_SPECS:
        if spec["estimand_family"] == "selected-conditional-feature":
            continue
        try:
            success = next(binomial_values)
        except StopIteration as exc:
            raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                "CP72_INTERNAL_INVARIANT_FAILED", "fixture binomial vector ended early"
            ) from exc
        if type(success) is not int:
            _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture success type differs")
        binomial_by_ordinal[spec["estimand_ordinal"]] = success
        if spec["estimand_family"] == "observable-cell":
            selected_label = (
                _REJECTION_OBSERVABLE_CELLS[0]
                if spec["strategy"] == "bounded-rejection"
                else _SIR_OBSERVABLE_CELLS[0]
            )
            if spec["observable_cell_label"] == selected_label:
                selected_by_row[cast(int, spec["row_ordinal"]) - 1] = success
    if any(value is None for value in selected_by_row):
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture selected inventory differs")
    records = []
    for spec, cp61_sha256 in zip(_ESTIMAND_SPECS, cp61_sha256s):
        if spec["estimand_family"] == "selected-conditional-feature":
            try:
                total = _qualification_fraction_pair(next(feature_values))
            except StopIteration as exc:
                raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                    "CP72_INTERNAL_INVARIANT_FAILED",
                    "fixture feature vector ended early",
                ) from exc
            success = None
        else:
            total = None
            success = cast(int, binomial_by_ordinal[spec["estimand_ordinal"]])
        records.append(
            _qualification_estimand_record(
                spec,
                cp61_sha256,
                success,
                cast(int, selected_by_row[cast(int, spec["row_ordinal"]) - 1]),
                total,
                endpoints,
            )
        )
    if len(records) != CP72_TEST28_ESTIMAND_COUNT:
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "fixture output count differs")
    output_root = dict(root)
    output_root["estimand_estimate_intervals"] = tuple(records)
    payload = _plain_json_bytes(output_root)
    fixture_index = CP72_TEST28_QUALIFICATION_FIXTURE_IDS.index(fixture_id)
    if fixture_index < len(_CP71_FIXTURE_OUTPUT_BYTES) and (
        len(payload) != _CP71_FIXTURE_OUTPUT_BYTES[fixture_index]
        or not hmac.compare_digest(
            hashlib.sha256(payload).hexdigest(),
            _CP71_FIXTURE_OUTPUT_SHA256S[fixture_index],
        )
    ):
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "exact CP71 fixture output differs")
    del records, output_root, data
    return payload


_QUALIFICATION_FIXTURE_SPECIFICATIONS = (
    "exact-cp71-output-for-cp69-closed-baseline",
    "exact-cp71-output-for-all-selected-duplicate-pair-plan-seeds",
    "exact-cp71-output-for-all-nonselected-cyclic-statuses",
    "exact-cp71-output-for-novel-k-mixed-selection",
    "cp72-owned-internally-valid-nonfixture-output-with-sixteen-new-success-counts",
)

_BUNDLE_LOCK = threading.RLock()
_BUNDLE_CACHE: Optional[
    CP72SuppliedDevelopmentOutputValidationQualificationBundleV1
] = None


def cp72_supplied_development_output_validation_qualification_bundle() -> CP72SuppliedDevelopmentOutputValidationQualificationBundleV1:
    """Return the zero-execution declarative CP72 contract bundle."""

    global _BUNDLE_CACHE
    with _BUNDLE_LOCK:
        if _BUNDLE_CACHE is None:
            _BUNDLE_CACHE = cast(
                CP72SuppliedDevelopmentOutputValidationQualificationBundleV1,
                _record(
                    CP72SuppliedDevelopmentOutputValidationQualificationBundleV1,
                    {
                        "schema_version": CP72_TEST28_SCHEMA_VERSION,
                        "scope": CP72_TEST28_SCOPE,
                        "blocker_ledger_prerequisite_id": CP72_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID,
                        "blocker_ledger_prerequisite_state": _LEDGER_PREREQUISITE_STATE,
                        "blocker_ledger_total_count": 27,
                        "blocker_ledger_satisfied_count": 23,
                        "blocker_ledger_missing_count": 4,
                        "predecessor_custody": _predecessor_custody(),
                        "validation_contract": _validation_contract(),
                        "qualification_fixture_ids": CP72_TEST28_QUALIFICATION_FIXTURE_IDS,
                        "qualification_fixture_specifications": _QUALIFICATION_FIXTURE_SPECIFICATIONS,
                        "zero_argument_builder": True,
                        "builder_validates": False,
                        "qualification_runner_zero_argument": True,
                        "public_supplied_output_validator_exposed": True,
                        "public_caller_data_api_count": 1,
                        "public_parser_exposed": False,
                        "public_stream_reducer_exposed": False,
                        "public_raw_record_api_exposed": False,
                        "public_stable_trace_api_exposed": False,
                        "public_path_api_exposed": False,
                        "public_writer_api_exposed": False,
                        "public_primary_decision_threshold_api_exposed": False,
                        "public_decision_api_exposed": False,
                        "public_receipt_or_evidence_api_exposed": False,
                        "project_modules_imported": False,
                        "source_independent": True,
                        "stdlib_only": True,
                        "production_execution_authorized": False,
                        "production_recomputation_qualified": False,
                        "unconditional_operational_predictions_produced": False,
                        "power_review_present": False,
                        "primary_thresholds_present": False,
                        "confirmatory_custody_present": False,
                        "runner_and_recomputation_blocker_closed": False,
                        "unconditional_operational_predictions_blocker_closed": False,
                        "power_and_thresholds_blocker_closed": False,
                        "confirmatory_custody_blocker_closed": False,
                        "formal_test_28_status": CP72_TEST28_FORMAL_TEST_28_STATUS,
                        "formal_test_28_closed": False,
                    },
                ),
            )
        return _BUNDLE_CACHE


def _verify_qualification_summary(
    fixture_index: int,
    summary: CP72SuppliedDevelopmentOutputValidationSummaryV1,
) -> None:
    expected_true = (
        "stream_commitment_coherence_verified",
        "canonical_json_verified",
        "schema_verified",
        "estimand_inventory_and_order_verified",
        "record_digests_verified",
        "cross_record_arithmetic_verified",
        "exact_interval_arithmetic_verified",
    )
    expected_false = (
        "input_stream_relation_verified",
        "input_provenance_authenticated",
        "source_law_verified",
        "production_attempt_validity_evaluated",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_made",
        "production_evidence",
    )
    if (
        summary.schema_version != CP72_TEST28_SCHEMA_VERSION
        or summary.source_output_schema_version != _CP71_OUTPUT_SCHEMA_VERSION
        or summary.request_count != CP72_TEST28_REQUEST_COUNT
        or summary.estimand_count != CP72_TEST28_ESTIMAND_COUNT
        or summary.ordered_cp61_inventory_crosswalk_sha256
        != _CP72_CP61_CROSSWALK_SHA256
        or summary.selected_counts_by_row
        != _QUALIFICATION_SELECTED_COUNTS[fixture_index]
        or summary.observable_row_sums
        != (CP72_TEST28_SEED_COUNT,) * CP72_TEST28_ROW_COUNT
        or summary.computed_interval_count
        != _QUALIFICATION_COMPUTED_INTERVAL_COUNTS[fixture_index]
        or summary.insufficient_selection_count
        != _QUALIFICATION_INSUFFICIENT_SELECTION_COUNTS[fixture_index]
        or summary.output_canonical_json_bytes
        != _QUALIFICATION_OUTPUT_BYTES[fixture_index]
        or not hmac.compare_digest(
            summary.output_canonical_json_sha256,
            _QUALIFICATION_OUTPUT_SHA256S[fixture_index],
        )
        or any(getattr(summary, name) is not True for name in expected_true)
        or any(getattr(summary, name) is not False for name in expected_false)
    ):
        _fail("CP72_INTERNAL_INVARIANT_FAILED", "qualification summary differs")


_QUALIFICATION_LOCK = threading.RLock()
_QUALIFICATION_CACHE: Optional[
    CP72SuppliedDevelopmentOutputValidationQualificationV1
] = None


def _run_qualification_uncached() -> CP72SuppliedDevelopmentOutputValidationQualificationV1:
    endpoints = _qualification_cp_endpoints()
    cp61_sha256s = _qualification_cp61_record_sha256s()
    summary_sha256s = []
    output_bytes = []
    output_sha256s = []
    selected_counts = []
    computed_counts = []
    insufficient_counts = []
    for fixture_index, fixture_id in enumerate(CP72_TEST28_QUALIFICATION_FIXTURE_IDS):
        payload = _build_qualification_fixture_output(
            fixture_id, endpoints, cp61_sha256s
        )
        summary = cp72_validate_supplied_cp71_development_output_bytes(payload)
        _verify_qualification_summary(fixture_index, summary)
        summary_sha256s.append(summary.record_sha256)
        output_bytes.append(summary.output_canonical_json_bytes)
        output_sha256s.append(summary.output_canonical_json_sha256)
        selected_counts.append(summary.selected_counts_by_row)
        computed_counts.append(summary.computed_interval_count)
        insufficient_counts.append(summary.insufficient_selection_count)
        del payload, summary
    fixture_set_body = {
        "fixture_ids": CP72_TEST28_QUALIFICATION_FIXTURE_IDS,
        "fixture_validation_summary_record_sha256s": tuple(summary_sha256s),
        "fixture_output_canonical_json_bytes": tuple(output_bytes),
        "fixture_output_canonical_json_sha256s": tuple(output_sha256s),
        "fixture_selected_counts_by_row": tuple(selected_counts),
        "fixture_computed_interval_counts": tuple(computed_counts),
        "fixture_insufficient_selection_counts": tuple(insufficient_counts),
    }
    fixture_set_sha256 = hashlib.sha256(
        _QUALIFICATION_FIXTURE_SET_DOMAIN
        + b"\0"
        + _plain_json_bytes(fixture_set_body, _MAXIMUM_SEALED_RECORD_BYTES)
    ).hexdigest()
    return cast(
        CP72SuppliedDevelopmentOutputValidationQualificationV1,
        _record(
            CP72SuppliedDevelopmentOutputValidationQualificationV1,
            {
                "schema_version": CP72_TEST28_SCHEMA_VERSION,
                "fixture_set_sha256": fixture_set_sha256,
                "fixture_ids": CP72_TEST28_QUALIFICATION_FIXTURE_IDS,
                "fixture_validation_summary_record_sha256s": tuple(summary_sha256s),
                "fixture_output_canonical_json_bytes": tuple(output_bytes),
                "fixture_output_canonical_json_sha256s": tuple(output_sha256s),
                "fixture_selected_counts_by_row": tuple(selected_counts),
                "fixture_computed_interval_counts": tuple(computed_counts),
                "fixture_insufficient_selection_counts": tuple(insufficient_counts),
                "fixture_count": len(CP72_TEST28_QUALIFICATION_FIXTURE_IDS),
                "module_owned_total_output_bytes": sum(output_bytes),
                "module_owned_peak_input_payload_count": 1,
                "module_owned_peak_parsed_output_count": 1,
                "maximum_simultaneously_materialized_estimand_record_count": 1_108,
                "module_owned_output_payload_or_body_cached": False,
                "caller_output_retained_after_successful_return": False,
                "sealed_summary_snapshot_retained_while_summary_live": True,
                "module_direct_filesystem_read": False,
                "module_direct_filesystem_write": False,
                "module_direct_clock_read": False,
                "module_direct_rng_used": False,
                "module_direct_network_used": False,
                "module_direct_subprocess_used": False,
                "source_independent": True,
                "stdlib_only": True,
                "input_stream_relation_verified": False,
                "provenance_authenticated": False,
                "production_recomputation_performed": False,
                "operational_prediction": False,
                "power_review_present": False,
                "primary_thresholds_present": False,
                "decision_path_qualified": False,
                "production_gate_13_state": "MISSING",
                "production_gate_14_state": "MISSING",
                "production_evidence_present_count": 0,
                "runner_and_recomputation_blocker_closed": False,
                "formal_test_28_closed": False,
                "all_development_qualification_checks_passed": True,
            },
        ),
    )


def cp72_run_supplied_development_output_validation_qualification() -> CP72SuppliedDevelopmentOutputValidationQualificationV1:
    """Run five module-owned development validations and cache scalar results."""

    global _QUALIFICATION_CACHE
    with _QUALIFICATION_LOCK:
        if _QUALIFICATION_CACHE is None:
            try:
                _QUALIFICATION_CACHE = _run_qualification_uncached()
            except CP72SuppliedDevelopmentOutputValidationQualificationError:
                raise
            except MemoryError as exc:
                raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                    "CP72_RESOURCE_EXHAUSTED", "qualification exhausted memory"
                ) from exc
            except (KeyboardInterrupt, SystemExit, GeneratorExit):
                raise
            except Exception as exc:
                raise CP72SuppliedDevelopmentOutputValidationQualificationError(
                    "CP72_INTERNAL_INVARIANT_FAILED", "qualification failed closed"
                ) from exc
        return _QUALIFICATION_CACHE


__all__ = (
    "CP72_TEST28_SCHEMA_VERSION",
    "CP72_TEST28_SCOPE",
    "CP72_TEST28_FORMAL_TEST_28_STATUS",
    "CP72_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
    "CP72_TEST28_SEED_COUNT",
    "CP72_TEST28_ROW_COUNT",
    "CP72_TEST28_REQUEST_COUNT",
    "CP72_TEST28_ESTIMAND_COUNT",
    "CP72_TEST28_OBSERVABLE_ESTIMAND_COUNT",
    "CP72_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT",
    "CP72_TEST28_FEATURE_ESTIMAND_COUNT",
    "CP72_TEST28_BINOMIAL_ESTIMAND_COUNT",
    "CP72_TEST28_FAMILYWISE_ERROR_BUDGET",
    "CP72_TEST28_PER_ESTIMATOR_ERROR_BUDGET",
    "CP72_TEST28_PER_TAIL_ERROR_BUDGET",
    "CP72_TEST28_CP_BISECTION_STEPS",
    "CP72_TEST28_MINIMUM_SELECTED_COUNT",
    "CP72_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER",
    "CP72_TEST28_MAXIMUM_OUTPUT_BYTES",
    "CP72_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES",
    "CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES",
    "CP72_TEST28_MAXIMUM_CANONICAL_DEPTH",
    "CP72_TEST28_MAXIMUM_CANONICAL_NODES",
    "CP72_TEST28_MAXIMUM_KEY_CHARACTERS",
    "CP72_TEST28_MAXIMUM_TEXT_CHARACTERS",
    "CP72_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS",
    "CP72_TEST28_MAXIMUM_FRACTION_DECIMAL_DIGITS",
    "CP72_TEST28_MAXIMUM_INTEGER_BITS",
    "CP72_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT",
    "CP72_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY",
    "CP72_TEST28_QUALIFICATION_FIXTURE_IDS",
    "CP72_TEST28_ERROR_CODES",
    "CP72SuppliedDevelopmentOutputValidationQualificationError",
    "CP72PredecessorCustodyV1",
    "CP72SuppliedDevelopmentOutputValidationContractV1",
    "CP72SuppliedDevelopmentOutputValidationSummaryV1",
    "CP72SuppliedDevelopmentOutputValidationQualificationV1",
    "CP72SuppliedDevelopmentOutputValidationQualificationBundleV1",
    "cp72_canonical_json_bytes",
    "cp72_sha256",
    "cp72_validate_supplied_cp71_development_output_bytes",
    "cp72_supplied_development_output_validation_qualification_bundle",
    "cp72_run_supplied_development_output_validation_qualification",
)
