---
title: "Pack 1 — one-page mathematical refresher"
tags: [wbr, control, lqr, mathematics, refresher]
---

# Toolkit — one-page refresher

Read once, then return to [[Pack 1 - LQR]]. This is a compact refresher, not a prerequisite course.

| Tool | What to remember | Why it appears here |
| --- | --- | --- |
| State vector | $x\in\mathbb R^n$ is a column; $u\in\mathbb R^m$. | WBR has six physical states and two aggregate inputs. |
| Matrix product | $A\in\mathbb R^{n\times n}$, $B\in\mathbb R^{n\times m}$; $Ax+Bu\in\mathbb R^n$. | Check dimensions before trusting an equation. |
| Transpose | $(Ax)^T=x^TA^T$. | Expanding the future quadratic cost. |
| Quadratic form | $x^TQx=\sum_i q_i x_i^2$ for diagonal $Q$. | Turns many tracking errors into a scalar cost. |
| Definiteness | $Q\succeq0$: $x^TQx\ge0$; $R\succ0$: $u^TRu>0$ for $u\ne0$. | Errors cannot earn negative cost; action minimization is strictly convex. |
| Gradient | For symmetric $P$, $\nabla_x(x^TPx)=2Px$. | Differentiate the Bellman minimization with respect to $u$. |
| Jacobian | $A_{ij}=\partial f_i/\partial x_j$, $B_{ij}=\partial f_i/\partial u_j$. | Local linearization of nonlinear robot dynamics. |
| Eigenpair | $Av=\lambda v$. | Each mode has a growth/decay factor. Discrete stability needs $|\lambda|<1$; continuous stability needs $\Re(\lambda)<0$. |
| Linear solve | Solve $Hu=b$; avoid explicitly forming $H^{-1}$. | Same mathematics, more robust numerical implementation. |
| Expectation | $\mathbb E[X]=\sum_x p(x)x$ in a discrete example. | Later RL averages uncertain future rewards; deterministic LQR here does not need sampling. |

## A 30-second units check

If tilt is in radians, $q_\theta\theta^2$ uses radians squared. Converting tilt to degrees without transforming its weight changes the optimization problem. To make a term dimensionless, normalize by a meaningful scale:

$$
q_\theta\theta^2
=w_\theta\left(\frac{\theta}{\theta_{\mathrm{scale}}}\right)^2,
\qquad q_\theta=\frac{w_\theta}{\theta_{\mathrm{scale}}^2}.
$$

> [!example] Check yourself
> $x=[0.02,0.1]^T$, $Q=\operatorname{diag}(40,200)$ gives $x^TQx=0.016+2=2.016$. A large coefficient alone does not tell you which physical error matters most; the error magnitude and units matter too.

**Diagnostic:** Can you explain why $B^TPB$ is $m\times m$, why $x^TPx$ is a scalar, and why an eigenvalue $1.01$ is unstable in discrete time? If yes, start the derivation.
