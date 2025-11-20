# PhysForge - Three Versions Explained

## Which version should you use?

| Feature | Demo<br>`app_simplified/` | Research Edition<br>`app_research/` | Production Platform<br>`backend/` |
|---------|---------------------------|-------------------------------------|-----------------------------------|
| **Purpose** | Quick proof-of-concept | Research tool for papers | Enterprise SaaS platform |
| **Target User** | Students, demos | Researchers, academics | Commercial/government |
| **Deployment** | ✅ Deployed at physforge.onrender.com | 🔄 Ready to deploy | ⚠️ Needs testing |
| **Cost** | Free (Render free tier) | $7/month (Starter instance) | $100+/month (multi-service) |
| | | |
| **Discovery Methods** | | |
| Sparse Regression | ✅ Yes (60-90s) | ✅ Yes (30-45s) | ✅ Yes |
| PySR Symbolic | ❌ No | ✅ Yes (2-3 min) | ✅ Yes |
| Model Comparison | ❌ No | ✅ AIC/BIC ranking | ✅ Full comparison |
| Active Learning | ❌ No | 🔄 Coming soon | ✅ Yes |
| | | |
| **PINN Features** | | |
| Basic Architecture | ✅ 2-20-20-1 | ✅ Configurable | ✅ Configurable |
| Fourier Features | ❌ No | 🔄 Coming soon | ✅ Yes |
| Multi-fidelity | ❌ No | ❌ No | ✅ Yes |
| GPU Support | ❌ CPU only | ❌ CPU only | ✅ GPU clusters |
| | | |
| **Usability** | | |
| Web Interface | ✅ Simple | ✅ Enhanced | ✅ Advanced |
| Real-time Logs | ✅ Yes | ✅ Yes | ✅ Yes |
| Result Export | ⚠️ Screenshot only | ✅ JSON/CSV | ✅ API + formats |
| Visualization | ✅ Basic plot | ✅ Enhanced plot | ✅ Interactive 3D |
| | | |
| **Deployment** | | |
| Setup Time | 5 minutes | 10 minutes | 2-3 days |
| Maintenance | None | Minimal | High |
| Scalability | 1 user at a time | 5-10 concurrent | Unlimited |
| | | |
| **Code Complexity** | | |
| Lines of Code | ~500 | ~800 | ~15,000 |
| Services | 1 (monolith) | 1 (monolith) | 10 (microservices) |
| Dependencies | 8 packages | 10 packages | 40+ packages |
| | | |
| **Research Value** | | |
| Publishable? | ⚠️ Maybe (basic) | ✅ Yes (novel) | ✅ Yes (comprehensive) |
| Differentiator | PINN + web UI | PINN + sparse + PySR | Full platform |
| Comparison | Worse than PySINDy | Better than existing tools | Production-grade |

## Decision Guide

### Use **Demo** (`app_simplified/`) if:
- ✅ You want to see how it works (5 min setup)
- ✅ Presenting to non-technical audience
- ✅ Teaching PINNs or equation discovery
- ✅ Testing on simple linear PDEs
- ✅ Zero budget

**Example Use Cases:**
- Class demonstration of PINN training
- Blog post showing equation discovery
- Quick feasibility check
- Student project

**Limitations:**
- Can't discover nonlinear terms (sin, exp, log)
- No model comparison
- No active learning

---

### Use **Research Edition** (`app_research/`) if:
- ✅ Writing a research paper
- ✅ Discovering unknown equations from data
- ✅ Need nonlinear/transcendental terms
- ✅ Want to compare multiple methods
- ✅ Can afford $7/month hosting

**Example Use Cases:**
- CFD: Discover turbulence closure models
- Climate: Parametrize sub-grid physics
- Materials: Find constitutive laws
- Biology: Discover growth kinetics

**Advantages over Demo:**
1. **PySR finds transcendental functions** - Can discover u_t = u·sin(u)
2. **Model comparison** - Ranks 10 candidate equations
3. **Better for papers** - Novel contribution (no existing tool combines PINN + PySR)

**Advantages over Production:**
1. **10-15 days of work** vs 8 weeks
2. **Research-focused** - Zero bloat from auth/multi-tenancy
3. **Simpler deployment** - Single service vs 10 microservices
4. **Faster iteration** - Modify and test in minutes

---

### Use **Production Platform** (`backend/`) if:
- ✅ Building commercial product
- ✅ Need multi-tenancy and auth
- ✅ Handling 100+ concurrent users
- ✅ Require GPU clusters
- ✅ Have engineering team

**Example Use Cases:**
- SaaS product for engineering firms
- Enterprise deployment for defense/aerospace
- High-throughput research facility
- Commercial simulation platform

**Requirements:**
- DevOps expertise (Kubernetes, monitoring)
- 2-3 months development time
- $500+/month infrastructure
- Team for maintenance

**When NOT to use:**
- ❌ Just writing a paper (overkill)
- ❌ Solo researcher (too complex)
- ❌ Proof-of-concept (use demo)

## Migration Path

```
Demo (5 min)
    ↓
    Test on your data
    ↓
Research Edition (1-2 weeks)  ← YOU ARE HERE
    ↓
    Publish paper
    ↓
    Get users/funding
    ↓
Production Platform (2-3 months)
    ↓
    Scale to commercial use
```

## Specific Recommendations

### For Academic Research Paper:
**Use Research Edition** - Gets you PySR discovery (the novel contribution) without production complexity.

Timeline:
- Week 1: Deploy research edition, test on datasets
- Week 2: Tune PySR settings, compare to baselines
- Week 3-4: Write paper, make figures
- Week 5: Submit to journal

### For PhD Thesis:
**Use Research Edition** - Sufficient for 1-2 thesis chapters on equation discovery.

Consider production platform if:
- Thesis focus is on the platform itself
- Need active learning for experiment design
- Building multi-user tool for lab

### For Grant Proposal:
**Use Research Edition** - Demonstrate feasibility with working tool.

Then:
- Include production platform in budget
- Justify GPU clusters for scaling
- Show path from prototype to production

### For Startup:
**Start with Research Edition** - Validate product-market fit first.

Then:
- Raise seed round
- Hire team
- Build production platform
- Scale infrastructure

### For Teaching:
**Use Demo** - Simple enough for students to understand.

Then:
- Assign research edition for projects
- Advanced students can contribute to production

## Current Status

| Version | Status | URL | Next Steps |
|---------|--------|-----|------------|
| **Demo** | ✅ Deployed | https://physforge.onrender.com | Maintenance only |
| **Research Edition** | 🔄 Development | - | 1. Test PySR<br>2. Deploy to Render<br>3. Write paper |
| **Production** | ⚠️ Untested | - | Needs 2-3 months work |

## Conclusion

**For most users reading this:** Use the **Research Edition**.

It gives you 90% of the research value (PySR, model comparison) with 10% of the complexity (no microservices, auth, etc.).

The production platform is valuable IF you're building a commercial product or need to support many concurrent users. But for publishing research, the research edition is sufficient and much faster to deploy.

---

**Questions?** See:
- [Research Edition Quick Start](app_research/QUICKSTART.md)
- [Research Edition README](app_research/README.md)
- [Deployment Guide](app_research/DEPLOYMENT.md)
