# Manuscript v3: exact F105 metric integration successor v2

**Status:** pre-outcome method-display successor  
**Primary metric:** `TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1`  
**Production projection:** `F105_CKS_BINARY64_PROJECTION_V1`

This additive successor replaces only the stale F105/CKS statements in
Sections 1, 5, and 8 of `manuscript_v3_locked_route_successor_v1.md`. All other
text in that predecessor remains current. Historical files remain evidence and
are not rewritten.

## Exact two-domain primary metric

Let \(d\in\{\mathrm{R3\mbox{-}PHYS},\mathrm{R4\mbox{-}RETAIL}\}\). For an
admitted event \(e\), let \(J_d(e)\in\mathbb R^{D_d}\) be the exact injective
domain map below, with \(D_{\mathrm{PHYS}}=112\) and
\(D_{\mathrm{RETAIL}}=10\). The event kernel is

\[
k_{E,d}(e,e')=\exp\!\left(-\frac{\lVert J_d(e)-J_d(e')\rVert_2^2}{2}\right).
\]

For an occurrence-expanded configuration \(x\), write \(n_x=x(E_d)\) and

\[
m_d(x)=
\begin{cases}
0, & n_x=0,\\[2mm]
\displaystyle \frac{1}{n_x}\sum_{e\in x} k_{E,d}(e,\cdot), & n_x>0.
\end{cases}
\qquad
\Phi_d(x)=(n_x,m_d(x)).
\]

All four squared parameters are exactly one:

\[
a_d^2=b_d^2=\tau_d^2=\sigma_d^2=1.
\]

Therefore the configuration kernel used in both confirmatory domains is

\[
k_{\Gamma,d}(x,x')=
\exp\!\left[-\frac{1}{2}\left\{
(n_x-n_{x'})^2+\lVert m_d(x)-m_d(x')\rVert_{\mathcal H_d}^2
\right\}\right].
\]

For \(2\le R\le128\) independent conditional draws \(X_1,\ldots,X_R\) and
target \(x\), the lower-is-better formal score is

\[
\widehat{\operatorname{CKS}}_d
=\frac{1}{R(R-1)}\sum_{r\ne r'}k_{\Gamma,d}(X_r,X_{r'})
-\frac{2}{R}\sum_{r=1}^{R}k_{\Gamma,d}(X_r,x).
\]

The confirmatory paired effect is

\[
\Delta_d=\widehat{\operatorname{CKS}}_{d,\mathrm{direct}}
-\widehat{\operatorname{CKS}}_{d,\mathrm{guide}},
\]

so positive \(\Delta_d\) favors the guide and equality is not favorable.
Cross-domain kernel evaluation is forbidden.

## PhysioNet event map

Let \(p\) be one of the frozen 37 time-series parameters, \(i(p)\) its
zero-based roster index, \(t\in\{0,\ldots,2880\}\) elapsed minutes, and \(v\)
either missing or an exact nonnegative value. With \(u_p\in\{0,1\}^{37}\) the
one-hot parameter vector, define

\[
J_{\mathrm{PHYS}}(t,p,v)=
\left(
u_p,
\frac{t}{2880},
\mathbf 1_{\{v\ \mathrm{present}\}}u_p,
\mathbf 1_{\{v\ \mathrm{present}\}}\frac{v}{1+v}u_p
\right)\in\mathbb R^{112}.
\]

The source token `-1` is missing and is distinct from a present zero. Source
decimal tokens are exact rationals; a binary64 adapter uses the exact
`as_integer_ratio` value. Multiplicity and simultaneous rows are preserved.
The configuration is all admitted time-series rows for one `RecordID` during
the first 48 hours. The per-configuration cap is \(2^{17}=131072\); exceeding
it or excluding any otherwise required patient/row is whole-domain `NO_GO`,
not truncation or reassignment.

## Online Retail II event map

For a finite UTF-8 byte string \(s=(b_1,\ldots,b_L)\), define

\[
c(s)=\frac{256^L-1}{255}+\sum_{i=1}^{L}b_i256^{L-i},
\qquad
J(s)=\frac{c(s)}{c(s)+1}.
\]

Let \(I\) be raw `InvoiceNo`, \(C(I)\) its frozen cancellation indicator,
\(S\) `StockCode`, \(D\) optional `Description`, \(u\) source-civil
microseconds since `2009-12-01 00:00:00`, \(q\) signed integer `Quantity`,
\(p\) exact-decimal `UnitPrice`, and \(G\) optional `Country`. With optional
presence masks \(m_D,m_G\in\{0,1\}\) and
\(H=63{,}849{,}600{,}000{,}000\) microseconds, define

\[
J_{\mathrm{RETAIL}}(I,S,D,u,q,p,G)=
\left(
J(I),C(I),J(S),m_D,m_DJ(D),\frac{u}{H},
\frac{q}{1+|q|},\frac{p}{1+|p|},m_G,m_GJ(G)
\right)\in\mathbb R^{10}.
\]

The horizon is the half-open source-civil interval
`[2009-12-01, 2011-12-10)`. No UTC, offset, daylight-saving, timezone, or
instant semantics are asserted. A configuration contains every admitted line
item for one canonical positive decimal `CustomerID`; duplicates, equal times,
and invoice multiplicity are retained. The conservative cap is 1,067,371 rows.
Cap overflow or exclusion of any otherwise required customer/row is
whole-domain `NO_GO`, with no truncation, top-up, resplit, or reassignment.

## Production evaluation binding

The production evaluator imports the frozen exact constructors and never
redefines the event maps or kernel. It builds the same canonical formal score,
whose terms have the form

\[
\sum_j \beta_j\exp\!\left[-\left(c_j+
\sum_\ell\alpha_{j\ell}e^{-q_{j\ell}}\right)\right],
\]

then projects only those exponentials and the final finite sum to binary64.
Every output records the exact formal-score SHA-256, binary64 hexadecimal
value, domain, draw count, metric ID, direction, and symbolic work count. The
supported audit records are factory-only and revalidate their derived digest,
numeric score, paired effect, and domain-separated integrity digest over all
public audit fields. A caller-visible default ceiling of
10,000,000 symbolic event-pair work units refuses before kernel evaluation
when exceeded; for a direct-versus-guide comparison the ceiling applies to the
combined work of both arms. The evaluator performs no
fitting, random drawing, parsing, file I/O, data access, thresholding, or
scientific decision.

The production source is
`src/heterodiff/evaluation/two_domain_count_normalized_event_cks_production.py`.
It is code-matched to the exact symbolic source
`src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py` through
formal-score equality tests in both domains.

## Remaining pre-outcome items and nonclaims

This successor completes the manuscript-display and production-evaluator
integration task only. It does not choose the confirmatory conditional draw
count (F109), minimum meaningful effect (F110), real--real floor (F111), or
confidence procedure (F112), and therefore does not by itself close B04. It
does not admit either dataset, execute a parser, open test data, train a model,
evaluate an empirical score, fill R1--R4, close a Formal Test or blocker,
promote a scientific claim, or authorize execution.

Public schema facts referenced by the exact maps come from the official
[PhysioNet Challenge 2012 v1.0.0](https://physionet.org/content/challenge-2012/1.0.0/)
and [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
documentation pages. Those documentation observations are not dataset
snapshots or admission receipts.
