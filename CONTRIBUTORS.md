# Contributors

This replication study was carried out by five contributors as a university course project (SE418: Large Language Models) at Uskudar University, 2026. Roles below follow the [CRediT](https://credit.niso.org/) attribution taxonomy.

| Contributor | GitHub | Roles |
|---|---|---|
| **Sherwan Ali** | [@SherwanAli0](https://github.com/SherwanAli0) | Methodology, Software (generation with raw-logit capture, Stage 2), Investigation (Colab A100/L4 runs, batching study), Validation, Writing - original draft |
| **Ipek Ucar** | [@ipekucr](https://github.com/ipekucr) | Project administration, Conceptualization, Software (integration / pipeline runner), Writing - review and editing |
| **Yaprak Sevinc Aldogan** | [@YaprakSevincAldogan](https://github.com/YaprakSevincAldogan) | Data curation (upstream dataset recovery, unified format, validation), Software (Stage 1), Writing - review and editing |
| **Yasmine Guidoum** | [@Dandyyass](https://github.com/Dandyyass) | Software (entropy computation and token-to-sentence alignment, Stage 3), Validation, Writing - review and editing |
| **Abdenour Hichem Guidoum** | - | Software (labeling port and evaluation, Stage 4), Formal analysis (Table I aggregation, classification metrics), Writing - review and editing |

All five contributors reviewed and approved the final results, the sanity test suite, and this README.

## Acknowledgements

- Joo, Lee, and Choi for the entropy-based sentence-level hallucination score we replicate.
- Ivgi, Yoran, Berant, and Geva for the three evaluation datasets and the open labeling protocol (github.com/Mivg/fallbacks, MIT).
- Meta, Alibaba/Qwen, and Google for the open-weight models.
- HuggingFace for transformers and the model hub.
