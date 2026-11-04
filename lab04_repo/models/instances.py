"""Екземпляри фреймів для тестів (усі значення умовні, крім реальних позначень генів BRCA1/BRCA2)."""
from models.frames import (Dataset, FilterRequest, GeneticTest, IndelVariant, Patient, Proband, Relative,
                           SNPVariant, TestOffer, Variant)

# (префікс факту, екземпляр)
SAMPLE_INSTANCES = [
    ("variant", SNPVariant(id="V-001", QD=30.2, FS=2.1, SOR=0.9, MQ=60.0, MQRankSum=0.1, ReadPosRankSum=0.3)),
    ("variant", SNPVariant(id="V-002", QD=1.4, FS=3.0, SOR=1.1, MQ=59.8)),
    ("variant", SNPVariant(id="V-003", QD=18.0, FS=72.5, SOR=2.2, MQ=58.0, at_exon_end=True)),
    ("variant", IndelVariant(id="V-004", QD=12.0, FS=110.0, SOR=2.0, MQ=60.0, ReadPosRankSum=-9.5)),
    ("variant", Variant(id="V-005", variant_type="INDEL", QD=9.5, FS=230.0, SOR=1.8, MQ=57.0)),
    ("dataset", Dataset(id="D-001", dataset_type="small_gene_panel", large_variant_set=True, has_curated_known_variants=True)),
    ("dataset", Dataset(id="D-002", dataset_type="whole_genome", large_variant_set=True, has_curated_known_variants=True)),
    ("request", FilterRequest(id="Q-001", filter_basis="QUAL")),
    ("proband", Proband(id="P-001", age=54, diagnosis="breast_cancer_female", variant_gene="BRCA1")),
    ("relative", Relative(id="R-001", age=52, relationship="full_sibling", wants_testing=True)),
    ("relative", Relative(id="R-002", age=15, relationship="child", wants_testing=True)),
    ("relative", Relative(id="R-003", age=70, relationship="aunt_uncle", available=False)),
    ("patient", Patient(id="P-002", age=61, diagnosis="ovarian_cancer", family_member_with_cancer=True)),
    ("test", GeneticTest(id="T-001", test_type="generic_cancer_panel", includes_family_variant=False, ordered_for_relative=True)),
    ("offer", TestOffer(id="O-001", time_limited=True)),
]
