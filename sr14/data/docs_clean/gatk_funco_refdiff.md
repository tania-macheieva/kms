## 0 - Introduction
This page explains the discrepancies between the different "hg19" references.

There are 4 common "hg19" references, and they are NOT directly interchangeable:
* **hg19** (`ucsc.hg19.fasta`, MD5sum: `a244d8a32473650b25c6e8e1654387d6`)
* **b37** (`Homo_sapiens_assembly19.fasta`, MD5sum: `886ba1559393f75872c1cf459eb57f2d`)
* **GRCh37** (`GRCh37.p13.genome.fasta`, MD5sum: `c140882eb2ea89bc2edfe934d51b66cc`)
* **humanG1Kv37** (`human_g1k_v37.fasta`, MD5sum: `0ce84c872fc0072a885926823dcd0338`)

### 0.1 - Table of Contents
0. 0.0 Introduction
 1. 0.1 Table of Contents
1. hg19
2. GRCh37
3. b37
4. HumanG1Kv37
5. Reference Comparison Table
6. Additional Information

## GRCh37
The Genome Reference Consortium Human Build 37, *GRCh37*, (`GRCh37.p13.genome.fasta`, MD5sum: `c140882eb2ea89bc2edfe934d51b66cc`) is a _Homo Sapiens_ genome reference file built by the Genome Reference Consortium. This is a baseline human genome reference and serves as the basis for the other three references in this comparison.

For more information on GRCh37, visit the official Genome Reference Consortium website.

## hg19
The University of California at Santa Cruz (UCSC) has created a reference based on GRCh37. This reference is often referred to as *hg19* (`ucsc.hg19.fasta`, MD5sum: `a244d8a32473650b25c6e8e1654387d6`).

This reference contains some alterations from the baseline reference from the Genome Reference Consortium. These alterations largely consist of contig name changes, however there are *known sequence differences on some contigs as well*.

For details see the comparison table.

## b37
The Broad Institute created a human genome reference file based on GRCh37. This reference is often referred to as *b37* (`Homo_sapiens_assembly19.fasta`, MD5sum: `886ba1559393f75872c1cf459eb57f2d`).

**When people at The Broad Institute's Genomics Platform refer to the _hg19_ reference, they are actually referring to `b37`.**

This reference contains some alterations from the baseline reference from the Genome Reference Consortium. These alterations largely consist of contig name changes, however there are *known sequence differences on some contigs as well*.

Anecdotally the changes are for bases for which there was low confidence. Those low confidence bases were then masked out in the `b37` reference to be the `IUPAC` symbol for any base. However, _there does not seem to be a detailed comparison readily available_.

For details see the comparison table.

## HumanG1Kv37
The *humanG1Kv37* (`human_g1k_v37.fasta`, MD5sum: `0ce84c872fc0072a885926823dcd0338`) reference is equivalent to b37, with the exception that it does not contain the decoy sequence for human herpesvirus 4 type 1 (named _NC_007605_).

## Reference Comparison Table

The specific differences between these four references are detailed in the following table.

The contigs with identical MD5sums are specified in each row. In the case that the MD5sum does not match between the references (indicating a sequence difference), the row will have a blank entry for that contig (`----`).

Primary contigs with differing MD5sums are highlighted in red.
Alternate contigs with differing MD5sums are highlighted in orange.

 MD5 HumanG1Kv37 Contig B37 Contig HG19 Contig GRCh37 Contig
 06cbf126247d89664a4faebad130fe9c GL000202.1 GL000202.1 chr11_gl000202_random GL000202.1
 0996b4475f353ca98bacb756ac479140 GL000244.1 GL000244.1 chrUn_gl000244 GL000244.1
 118a25ca210cfbcdfb6c2ebb249f9680 GL000235.1 GL000235.1 chrUn_gl000235 GL000235.1
 131b1efc3270cc838686b54e7c34b17b GL000238.1 GL000238.1 chrUn_gl000238 GL000238.1
 1c1b2cd1fccbc0a99b6a447fa24d1504 GL000226.1 GL000226.1 chrUn_gl000226 GL000226.1
 1d708b54644c26c7e01c2dad5426d38c GL000218.1 GL000218.1 chrUn_gl000218 GL000218.1
 1d78abec37c15fe29a275eb08d5af236 GL000249.1 GL000249.1 chrUn_gl000249 GL000249.1
 2f8694fc47576bc81b5fe9e7de0ba49e GL000242.1 GL000242.1 chrUn_gl000242 GL000242.1
 3238fb74ea87ae857f9c7508d315babb GL000221.1 GL000221.1 chrUn_gl000221 GL000221.1
 325ba9e808f669dfeee210fdd7b470ac GL000192.1 GL000192.1 chr1_gl000192_random GL000192.1
 399dfa03bf32022ab52a846f7ca35b30 GL000223.1 GL000223.1 chrUn_gl000223 GL000223.1
 3e06b6741061ad93a8587531307057d8 GL000232.1 GL000232.1 chrUn_gl000232 GL000232.1
 43f69e423533e948bfae5ce1d45bd3f1 GL000206.1 GL000206.1 chr17_gl000206_random GL000206.1
 445a86173da9f237d7bcf41c6cb8cc62 GL000240.1 GL000240.1 chrUn_gl000240 GL000240.1
 46c2032c37f2ed899eb41c0473319a69 GL000214.1 GL000214.1 chrUn_gl000214 GL000214.1
 563531689f3dbd691331fd6c5730a88b GL000212.1 GL000212.1 chrUn_gl000212 GL000212.1
 569af3b73522fab4b40995ae4944e78e GL000199.1 GL000199.1 chr9_gl000199_random GL000199.1
 5a8e43bec9be36c7b49c84d585107776 GL000248.1 GL000248.1 chrUn_gl000248 GL000248.1
 5d9ec007868d517e73543b005ba48535 GL000195.1 GL000195.1 chr7_gl000195_random GL000195.1
 5eb3b418480ae67a997957c909375a73 GL000215.1 GL000215.1 chrUn_gl000215 GL000215.1
 63945c3e6962f28ffd469719a747e73c GL000225.1 GL000225.1 chrUn_gl000225 GL000225.1
 642a232d91c486ac339263820aef7fe0 GL000216.1 GL000216.1 chrUn_gl000216 GL000216.1
 6ac8f815bf8e845bb3031b73f812c012 GL000194.1 GL000194.1 chr4_gl000194_random GL000194.1
 6d243e18dea1945fb7f2517615b8f52e GL000217.1 GL000217.1 chrUn_gl000217 GL000217.1
 6f5efdd36643a9b8c8ccad6f2f1edc7b GL000197.1 GL000197.1 chr8_gl000197_random GL000197.1
 6fe9abac455169f50470f5a6b01d0f59 GL000222.1 GL000222.1 chrUn_gl000222 GL000222.1
 75e4c8d17cd4addf3917d1703cacaf25 GL000200.1 GL000200.1 chr9_gl000200_random GL000200.1
 7daaa45c66b288847b9b32b964e623d3 GL000211.1 GL000211.1 chrUn_gl000211 GL000211.1
 7de00226bb7df1c57276ca6baabafd15 GL000247.1 GL000247.1 chrUn_gl000247 GL000247.1
 7e0e2e580297b7764e31dbc80c2540dd X X chrX chrX
 7fed60298a8d62ff808b74b6ce820001 GL000233.1 GL000233.1 chrUn_gl000233 GL000233.1
 851106a74238044126131ce2a8e5847c GL000210.1 GL000210.1 chr21_gl000210_random GL000210.1
 868e7784040da90d900d2d1b667a1383 GL000198.1 GL000198.1 chr9_gl000198_random GL000198.1
 89bc61960f37d94abf0df2d481ada0ec GL000245.1 GL000245.1 chrUn_gl000245 GL000245.1
 93f998536b61a56fd0ff47322a911d4b GL000234.1 GL000234.1 chrUn_gl000234 GL000234.1
 96358c325fe0e70bee73436e8bb14dbd GL000203.1 GL000203.1 chr17_gl000203_random GL000203.1
 99795f15702caec4fa1c4e15f8a29c07 GL000239.1 GL000239.1 chrUn_gl000239 GL000239.1
 9d424fdcc98866650b58f004080a992a GL000213.1 GL000213.1 chrUn_gl000213 GL000213.1
 a4aead23f8053f2655e468bcc6ecdceb GL000227.1 GL000227.1 chrUn_gl000227 GL000227.1
 aa81be49bf3fe63a79bdc6a6f279abf6 GL000208.1 GL000208.1 chr19_gl000208_random GL000208.1
 b4eb71ee878d3706246b7c1dbef69299 GL000230.1 GL000230.1 chrUn_gl000230 GL000230.1
 ba8882ce3a1efa2080e5d29b956568a4 GL000231.1 GL000231.1 chrUn_gl000231 GL000231.1
 c5a17c97e2c1a0b6a9cc5a6b064b714f GL000228.1 GL000228.1 chrUn_gl000228 GL000228.1
 cc34279a7e353136741c9fce79bc4396 GL000243.1 GL000243.1 chrUn_gl000243 GL000243.1
 d0f40ec87de311d8e715b52e4c7062e1 GL000229.1 GL000229.1 chrUn_gl000229 GL000229.1
 d22441398d99caf673e9afb9a1908ec5 GL000205.1 GL000205.1 chr17_gl000205_random GL000205.1
 d5b2fc04f6b41b212a4198a07f450e20 GL000224.1 GL000224.1 chrUn_gl000224 GL000224.1
 d75b436f50a8214ee9c2a51d30b2c2cc GL000191.1 GL000191.1 chr1_gl000191_random GL000191.1
 d92206d1bb4c3b4019c43c0875c06dc0 GL000196.1 GL000196.1 chr8_gl000196_random GL000196.1
 dbb6e8ece0b5de29da56601613007c2a GL000193.1 GL000193.1 chr4_gl000193_random GL000193.1
 dfb7e7ec60ffdcb85cb359ea28454ee9 GL000201.1 GL000201.1 chr9_gl000201_random GL000201.1
 e0c82e7751df73f4f6d0ed30cdc853c0 GL000237.1 GL000237.1 chrUn_gl000237 GL000237.1
 e4afcd31912af9d9c2546acf1cb23af2 GL000246.1 GL000246.1 chrUn_gl000246 GL000246.1
 ef4258cdc5a45c206cea8fc3e1d858cf GL000241.1 GL000241.1 chrUn_gl000241 GL000241.1
 efc49c871536fa8d79cb0a06fa739722 GL000204.1 GL000204.1 chr17_gl000204_random GL000204.1
 f3814841f1939d3ca19072d9e89f3fd7 GL000207.1 GL000207.1 chr18_gl000207_random GL000207.1
 f40598e2a5a6b26e84a3775e0d1e2c81 GL000209.1 GL000209.1 chr19_gl000209_random GL000209.1
 f977edd13bac459cb2ed4a5457dba1b3 GL000219.1 GL000219.1 chrUn_gl000219 GL000219.1
 fc35de963c57bf7648429e6454f1c9db GL000220.1 GL000220.1 chrUn_gl000220 GL000220.1
 fdcd739913efa1fdc64b6c0cd7016779 GL000236.1 GL000236.1 chrUn_gl000236 GL000236.1
 1b22b98cdeb4a9304cb5d48026a85128 1 1 chr1 chr1
 a0d9851da00400dec1098a9255ac712e 2 2 chr2 chr2
 23dccd106897542ad87d2765d28a19a1 4 4 chr4 chr4
 0740173db9ffd264d728f32784845cd7 5 5 chr5 chr5
 1d3a93a248d92a729ee764823acbbc6b 6 6 chr6 chr6
 618366e953d6aaad97dbe4777c29375e 7 7 chr7 chr7
 96f514a9929e410c6651697bded59aec 8 8 chr8 chr8
 3e273117f15e0a400f01055d9f393768 9 9 chr9 chr9
 988c28e000e84c26d552359af1ea2e1d 10 10 chr10 chr10
 98c59049a2df285c76ffb1c6db8f8b96 11 11 chr11 chr11
 51851ac0e1a115847ad36449b0015864 12 12 chr12 chr12
 283f8d7892baa81b510a015719ca7b0b 13 13 chr13 chr13
 98f3cae32b2a2e9524bc19813927542e 14 14 chr14 chr14
 e5645a794a8238215b2cd77acb95a078 15 15 chr15 chr15
 fc9b1a7b42b97a864f56b348b06095e6 16 16 chr16 chr16
 351f64d4f4f9ddd45b35336ad97aa6de 17 17 chr17 chr17
 b15d4b2d29dde9d3e4f93d1d0f2cbc9c 18 18 chr18 chr18
 1aacd71f30db8e561810913e0b72636d 19 19 chr19 chr19
 0dec9660ec1efaaf33281c0d5ea2560f 20 20 chr20 chr20
 2979a6085bfe28e3ad6f552f361ed74d 21 21 chr21 chr21
 a718acaa6135fdca8357d5bfe94211dd 22 22 chr22 chr22
 1fa3474750af0948bdf97d5a0ee52e51 Y Y ---- ----
 6743bd63b3ff2b5b8985d8933c53290a ---- NC_007605 ---- ----
 c68f52674c9fb33aef52dcf399755519 MT MT ---- chrM
 fdfd811849cc2fadebc929bb925902e5 3 3 ---- ----
 094d037050cad692b57ea12c4fef790f ---- ---- chr6_qbl_hap6 GL000255.1
 18c17e1641ef04873b15f40f6c8659a4 ---- ---- chr6_cox_hap2 GL000251.1
 1e86411d73e6f00a10590f976be01623 ---- ---- chrY chrY
 2a3c677c426a10e137883ae1ffb8da3f ---- ---- chr6_dbb_hap3 GL000252.1
 3b6d666200e72bcc036bf88a4d7e0749 ---- ---- chr6_ssto_hap7 GL000256.1
 641e4338fa8d52a5b781bd2a2c08d3c3 ---- ---- chr3 chr3
 9d51d4152174461cd6715c7ddc588dc8 ---- ---- chr6_mann_hap4 GL000253.1
 d2ed829b8a1628d16cbeee88e88e39eb ---- ---- chrM ----
 d89517b400226d3b56e753972a7cad67 ---- ---- chr17_ctg5_hap1 GL000258.1
 efed415dd8742349cb7aaca054675b9a ---- ---- chr6_mcf_hap5 GL000254.1
 fa24f81b680df26bcfb6d69b784fbe36 ---- ---- chr4_ctg9_hap1 GL000257.1
 fe71bc63420d666884f37a3ad79f3317 ---- ---- chr6_apd_hap1 GL000250.1
 0386df1d3476e6649f919195cc072fc7 ---- ---- ---- GL383574.1
 03de7a950b56720768373120bbddf693 ---- ---- ---- GL383558.1
 03f5fa89e52d0fe155d2e3968bf2eeb7 ---- ---- ---- GL339450.1
 049056a72b5aee0b3f876ddf554f0208 ---- ---- ---- JH720447.1
 063358c8e7f81361b959efab7b3f15cc ---- ---- ---- GL383565.1
 07f56906bd56829f146dc0bf4b158603 ---- ---- ---- GL383538.1
 09ce2d45f1f973e347e22ad1e3cf06fb ---- ---- ---- GL383568.1
 09d4cb1070e1c521d6e86e7038824c1c ---- ---- ---- GL383544.1
 0aee7c3e4bcc4c942230508c7836069b ---- ---- ---- GL582967.1
 0bdfd2a40e1ceab32d71d6f1c9a6ca32 ---- ---- ---- JH636056.1
 0c787911df2449cbba8609bebf897ecb ---- ---- ---- GL383541.1
 0d12851232bcd8250e6dd61e3e7fd6a2 ---- ---- ---- JH636054.1
 0db85f8e0ff66a470b46801c9892e471 ---- ---- ---- JH806589.1
 0de582e28ae8c127d978b43e12a4f499 ---- ---- ---- KE332500.1
 0f0364ed52ebe7757feea96ce623239f ---- ---- ---- GL383529.1
 10b523cdfd4f3707276ec92f0f9cddfb ---- ---- ---- JH159133.1
 1135da7b213739cfb3bdf2741c0c8083 ---- ---- ---- KE332506.1
 122be4e189778434d8845fd5fd2c9a6b ---- ---- ---- GL949748.1
 12406aad3f3da31bda9c21a1aa0e16b6 ---- ---- ---- GL383539.1
 12a3180640a49f33c960eb12ca61a6c4 ---- ---- ---- GL383542.1
 13a8dc0d93c1bf1ae397593eba841721 ---- ---- ---- JH806573.1
 1452be48789c27311d94561610f6d5af ---- ---- ---- JH159132.1
 157eecba5817aa1781a7bc4a9b60f933 ---- ---- ---- JH720446.1
 15a2182cf9d3a55a7809adadc0775e03 ---- ---- ---- JH636060.1
 16197ace4bfafdc2354857b98fc2a794 ---- ---- ---- GL582971.1
 1668b0eb03be297f66837b46b5b73ac7 ---- ---- ---- JH806600.2
 16a9ef53c176dcd2cf029940cbc29382 ---- ---- ---- JH720452.1
 18c01f6e62136005ce1b2f2f33173f02 ---- ---- ---- GL582974.1
 18fd9605f12ec0982adcf9e908f53331 ---- ---- ---- GL383523.1
 190b4d20cab29ddba5f2495a7117f7cf ---- ---- ---- JH636055.1
 1919a95f3ea48fde56ba925295086028 ---- ---- ---- GL383582.2
 192dead6bc331a0dcbd1ba9d3d8a6f80 ---- ---- ---- JH806581.1
 1b6fa375fdf382778e6645d822d12254 ---- ---- ---- GL339449.2
 1d217e666c48ef7f2ec81946f4f4bfcc ---- ---- ---- GL383521.1
 1d2933992f087a832718c9de19d4ceab ---- ---- ---- KE332499.1
 20d5046bbd2a21729fdd64fa94bdd5a1 ---- ---- ---- GL949742.1
 20da91baf79b2e14b605a8ebe1f3704e ---- ---- ---- GL877872.1
 2118ff7bca8f75acc4629ab88bae1c2e ---- ---- ---- GL582968.1
 23aea04f46682e2a2be1a5ff3934a9fe ---- ---- ---- GL383540.1
 24f6ccbfc261e62451042a9713be6280 ---- ---- ---- JH636059.1
 2536c2286fdeb98404ac410dbf528a3e ---- ---- ---- GL949745.1
 260aca5e1ff29b6ed3d3cd9e438f4219 ---- ---- ---- JH636053.3
 2948653361f974fbed3e26a4dfbf332c ---- ---- ---- GL383528.1
 2cfa9ec8f70be88f95411dac6efb24c1 ---- ---- ---- JH159141.2
 2e0bec27cfa9b440c746be52187fab0b ---- ---- ---- GL383560.1
 2f4f58e3b3a95bed1132833156340778 ---- ---- ---- GL383555.1
 2fc316247e162f76a01012bbd9b665e6 ---- ---- ---- JH806603.1
 321b3324431ae40e90a4117ecc07e93c ---- ---- ---- JH591185.1
 32ceefe714becfd36f207c5bffca4ba7 ---- ---- ---- GL877871.1
 3342f6c21fa2dc364925712e0d52ed2d ---- ---- ---- JH159148.1
 348782844074360bdc8b6416e16cc5d0 ---- ---- ---- GL383549.1
 349e96f115f829409bd1087b5fb684ca ---- ---- ---- GL383519.1
 35889722e6212fc9499e06e630268101 ---- ---- ---- JH806588.1
 369f03e72d44461eab4542c58f3b5dcc ---- ---- ---- KE332501.1
 384b5b32f0ea2cfd15ac268a2ce07909 ---- ---- ---- JH159146.1
 3893d44dfad7ce35744b2bde1e43bbd3 ---- ---- ---- GL383576.1
 38e72cd57edb75d967ac2613d61d297d ---- ---- ---- GL383563.2
 3b40b7fdb005a1ce00efaa3310148852 ---- ---- ---- KE332502.1
 3c5f20fb0744b7658d37d4ed79a286d1 ---- ---- ---- GL383520.1
 3dd30a7638c3a3c518fc15571546b1be ---- ---- ---- GL877875.1
 3e0825dd23c9fce74a88d863e33c42b7 ---- ---- ---- JH159149.1
 40015159c7da8f06875bb558587e3f07 ---- ---- ---- GL383571.1
 404580d8ad56ded0fb33642c8b99c28b ---- ---- ---- GL383537.1
 4112dee892050e18ad279b8ebdcc5d48 ---- ---- ---- GL383578.1
 41cf432193561894813a30da6e682e5b ---- ---- ---- KB021647.1
 447fe0ff3103170150280c775095eebf ---- ---- ---- JH806593.1
 44d5da56e5ec6ae0b9ebd354e9b47cfa ---- ---- ---- JH159150.3
 474baa8f6c6684c55bbc2a10bfa84baf ---- ---- ---- GL949747.1
 4791ba11d768da2cc1346d37a558047a ---- ---- ---- GL582972.1
 485c442c93fe19514153702f0c84d952 ---- ---- ---- GL582966.2
 4a3d54bda53308ca941d6d0e794b05cb ---- ---- ---- GL383554.1
 4ad67c3a4e85f8b2cd54a8ef2aab4426 ---- ---- ---- GL383557.1
 4bc4f02a4fca2c9d70646455bee8066e ---- ---- ---- JH806596.1
 50fd52ddb8ad2b024fb8b83a5c90a642 ---- ---- ---- JH806577.1
 5404455aab275489bc8e6c9fb3ead5cb ---- ---- ---- GL383573.1
 54abe159678a84e88ceb2d5271027628 ---- ---- ---- KB663609.1
 5835d9de56b65cefb9406d104d64531e ---- ---- ---- GL383536.1
 5950c02594cedbdf0fea5e8335e7cf80 ---- ---- ---- JH591181.2
 5b90c3ac4e5938b400fcc2c29f3017bc ---- ---- ---- GL949744.1
 5b9d9fb059071e552bba531b81bd3472 ---- ---- ---- KB663606.1
 5c3a364520bf7ed46894abdce8f6e032 ---- ---- ---- GL877876.1
 5eb6da458990f121fae13ff83a4bcbca ---- ---- ---- JH806576.1
 5f9dc3f86463d08a1383cca5f285b7ad ---- ---- ---- GL383570.1
 5fae03628eb9a445571bac107823b394 ---- ---- ---- KE332505.1
 620913159e2fbd4e931ac120e3c584c9 ---- ---- ---- GL383526.1
 659b65783878ace88f4c4b165f239363 ---- ---- ---- JH636052.4
 675046e52613269a7c2e803525bb5a33 ---- ---- ---- JH720445.1
 67f26a755ca4c6ca9a8f567d80d15fb9 ---- ---- ---- JH159131.1
 68391fb8f16a37b63f607b76702de3b1 ---- ---- ---- GL383583.1
 69490aa24b00717f2b11c095a5339516 ---- ---- ---- JH720454.3
 6b604cf3e324680b72716e814d805944 ---- ---- ---- GL383530.1
 6b862a953dfe724a1f48eaf12a3b948a ---- ---- ---- JH806578.1
 6c22616c927261b8e5fc90028c780f00 ---- ---- ---- JH720444.2
 6cba57c0e509ab785d3869134979b668 ---- ---- ---- GL383548.1
 6d728406957c5c7fb158dbdb7efef2b7 ---- ---- ---- GL383527.1
 6d85d704338ba29941aca4d278c7eb4a ---- ---- ---- KB663608.1
 6fbc7007a5ff8aae8b28ca52dd6d5571 ---- ---- ---- GL383531.1
 71a0d13c09c3e7ee64c7740e1425f20e ---- ---- ---- JH591183.1
 73b240dd73b8bddcab281e265c9d759a ---- ---- ---- GL383559.2
 73d39b5d51e6e2e8d9549bb85d7dae04 ---- ---- ---- JH806579.1
 741179e4ee12c60fbcc6eba4a5c7695b ---- ---- ---- JH806598.1
 74cff045a9cd92b7f571a756f248d16a ---- ---- ---- GL383524.1
 7b556f03729e304a286c8d7ef0f0c10e ---- ---- ---- GL383547.1
 7b6d6d01c18e91fc07f727ade2450f46 ---- ---- ---- JH806580.1
 7d007a35ff02e56325881c68bb17b565 ---- ---- ---- GL949752.1
 7e0afbdc97540aa0b101228b7bd331fb ---- ---- ---- JH806591.1
 8213c58e2c1c22397f0ad9d0d901bbdf ---- ---- ---- JH159135.2
 856a46516332f58a35eeb4f84d17febc ---- ---- ---- JH159142.2
 883b29a1e5975e0f3139c183fbe2596d ---- ---- ---- GL383581.1
 8a92722deabdf885d1aebfa8881d5903 ---- ---- ---- GL949753.1
 8ac2dc8046e4bd0d6d46e827ff05ecd1 ---- ---- ---- JH806575.1
 8ac9fb9d942dba38bfd30f8d767f4bba ---- ---- ---- JH159136.1
 8b1d46e46d3083625eac92e9363773dd ---- ---- ---- KB663607.2
 8d13c3e7cbb2b7e1a3225c5a54fe8f44 ---- ---- ---- GL383569.1
 8e1004755b0574b2f855130c943fbd8e ---- ---- ---- KB663603.1
 8e4f862d5b37504199902c6685b7fee5 ---- ---- ---- GL383533.1
 8ede6eec21d781c22a9801f51433fcd6 ---- ---- ---- JH806584.1
 8fc7aaa775b43df3d77c9782a140a981 ---- ---- ---- GL383572.1
 902d62224f09e59cb9c6c44f71b5fca3 ---- ---- ---- GL383580.1
 90ad438579d919fd20c42bb4f48de64b ---- ---- ---- JH591184.1
 9133580f75d0ffa745af12953d65a4db ---- ---- ---- GL383550.1
 93001afcfc8594885490513c4ffe243e ---- ---- ---- GL582977.2
 93a798f03267e553445c7456c6f7ee49 ---- ---- ---- JH159143.1
 94409f94ca59e67f811cd36ab133a82c ---- ---- ---- GL877873.1
 955e16dfcdb2d28a334349dfa39f2ed4 ---- ---- ---- KB021645.1
 976c3a7c4051dd9ce879833f4a764289 ---- ---- ---- JH806590.2
 978987018f1a910273ebcc387e038de8 ---- ---- ---- GL383518.1
 9bb3fbcd1fc9c35884e0987755c55667 ---- ---- ---- GL949741.1
 9bed9883963242dd74b883218d5f17bf ---- ---- ---- GL383532.1
 9d197695e8a47d4c30c891a53a0fd588 ---- ---- ---- JH720451.1
 9dcedb7219aa23057244ca9a446f01ac ---- ---- ---- JH806592.1
 9e1fc7ed55646756ce109b12b82ff192 ---- ---- ---- JH159147.1
 a009cf3116a844d7b2d467e672931bc5 ---- ---- ---- GL383564.1
 a0584071d5a8e88fda38d4cca38704cb ---- ---- ---- KB663605.1
 a0bce2b33eb96adcb750622527225e7d ---- ---- ---- JH720443.2
 a0f25165c6537c9861cc1231f710e99f ---- ---- ---- GL383566.1
 a1dab5e9bbedd3539ace29af1f9d6139 ---- ---- ---- JH806595.1
 a260ca7327d292deefef4f5fc7346dc4 ---- ---- ---- GL383561.2
 a2ecd2eb53eb1737423d5a637e4374a9 ---- ---- ---- JH636058.1
 a3bf927c2422ea0a661640669efd1081 ---- ---- ---- GL383577.1
 a4053747fc0cf1e03fa6ae9cd5f821d0 ---- ---- ---- KB021648.1
 aa5b0a15acec3c6177db764bd103d8a0 ---- ---- ---- JH720453.1
 ab73a8d586ef4fc44dd063730b6aef39 ---- ---- ---- GL582973.1
 abb9297c8b9dfc3013d416c803ff486c ---- ---- ---- JH806601.1
 ac9c384b2fc322b684128f1baf75785e ---- ---- ---- JH591182.1
 adb23c033121d433739de02cfa00c9fb ---- ---- ---- JH806582.2
 adec63ae44a39d716808cfee03b7a870 ---- ---- ---- JH806599.1
 afb0d13ed9fa7518989caa0ec55aeb96 ---- ---- ---- GL949750.1
 b293c854ddcbc316cb1d449bca46fbb3 ---- ---- ---- JH159137.1
 b8864877618b25fc14f80e8538f23b77 ---- ---- ---- GL949751.1
 b96f5e6bc844e8392d4e442aa7557e15 ---- ---- ---- KE332495.1
 ba6a3b1599661e674918200a8d1333d3 ---- ---- ---- JH806594.1
 bc6f64b0c4c934c2cea52bbe98639c79 ---- ---- ---- JH806583.1
 bc79d1abee7076ea672293e12bd7ccb9 ---- ---- ---- GL383517.1
 bd742a610e4bbc28fc00aaf71dfdc15d ---- ---- ---- KB021644.1
 be51fd8c00d62c3efc077a8e882062a4 ---- ---- ---- JH806586.1
 bed6a2667e8452a176e93e921e0c21f6 ---- ---- ---- GL383556.1
 c27dc6fea378fecf178a44682257c25e ---- ---- ---- GL383545.1
 c28f12c6ee0dec4cc6995766a710960c ---- ---- ---- GL383552.1
 c6ff49147dedce02366d6ade10580611 ---- ---- ---- GL383534.2
 c86ffa095c924372aa455e43e61c96e8 ---- ---- ---- JH159145.1
 ca0e3270f27bbee944844e44ec76659d ---- ---- ---- JH806602.1
 caebc01e3f44f7b2a559179b0261b77e ---- ---- ---- GL383535.1
 cca1c60136ec678eeef374134cd07a90 ---- ---- ---- GL877877.2
 cdab95f32513753b3c0add3014afad3b ---- ---- ---- JH806587.1
 d08cc284ad35f0bd1eafb443c23ad8bd ---- ---- ---- JH159138.1
 d0b63f9cef6c4d382e49636465eab851 ---- ---- ---- GL877870.2
 d0caa7bf982cf1e6ca8c8b833f56a21c ---- ---- ---- JH806597.1
 d4e2cf05984db16a78c953b898f5a86e ---- ---- ---- GL582969.1
 d76e635e75bc038782fb3d0c195d33fb ---- ---- ---- GL949746.1
 d8ef242a7373ff5657c8311b92dabfde ---- ---- ---- JH591186.1
 d9015dd9a0916a98ed8ab99fd3cdd012 ---- ---- ---- GL383567.1
 d96719c32333013a51c4d6d3261f984f ---- ---- ---- GL383551.1
 d97cf75e24ed1370388fedf523faa7ab ---- ---- ---- KE332496.1
 da648c938f1bb43b41d254bd9a015cfb ---- ---- ---- JH159139.1
 dada6dd12ec844a3a13f547f4946428e ---- ---- ---- JH159140.1
 dd0bc538e31f35af2073daec1f378147 ---- ---- ---- JH159144.1
 dd784bb8074d6f5b949464ffea8c6901 ---- ---- ---- JH720449.1
 dd8730d9d33765ff135fcfadb8810280 ---- ---- ---- GL383575.2
 df3e809f9a87f792218db18db51f6ad4 ---- ---- ---- GL383522.1
 e0da36f2d1d2c6092f13d5bee52537e0 ---- ---- ---- GL383516.1
 e0e934bd79ff323b31f4c9b80fb80a5c ---- ---- ---- JH159134.2
 e11adfbb638e60f61d7e8ef6647f30f2 ---- ---- ---- JH720448.1
 e2cd68e2099fbd7cee557d6a7910768f ---- ---- ---- KB021646.2
 e363729ea23dad7c6802e7b439b4f668 ---- ---- ---- KE332497.1
 e5b96eb9510763261839281c198607dd ---- ---- ---- GL582979.2
 e5cd94b0e0668debf81b82f405597b28 ---- ---- ---- GL582970.1
 e6c232469067e8cadfa852a2ea5513b7 ---- ---- ---- GL949749.1
 e8c870267b2a5261edb9d51d0efd6469 ---- ---- ---- GL582975.1
 ebf72aeb4d53f0fd56e2e72967751f8a ---- ---- ---- GL383562.1
 ed6bcd4459b3bc6b366ce00262952f57 ---- ---- ---- GL949743.1
 ed6fb45e0a25c31903cbb0f78d9d487e ---- ---- ---- GL383546.1
 edf086bce359065367b105cae0abfeee ---- ---- ---- GL383579.1
 edf41bfaf2584364bb4c5a645d73d53c ---- ---- ---- GL383553.2
 f2bfb99f84f2dd2ea538fe69ee786a0d ---- ---- ---- GL383525.1
 f486a5a44493d2e6bf72bf95ae898e3c ---- ---- ---- JH806574.2
 f7ee47af8d462cd9aeb6d40de99acb36 ---- ---- ---- JH806585.1
 fa5fa49d281fc855dd1076c4f51bd8dc ---- ---- ---- KE332498.1
 faa48b73103366d1da02065870a58bda ---- ---- ---- GL383543.1
 faae4c952e9c38254538e1853b786276 ---- ---- ---- GL582976.1
 fc93038463f9660e139435537ef53a5c ---- ---- ---- KB663604.1
 fdeb8db11e8544a638179a592c051331 ---- ---- ---- JH636061.1
 fef0bc815f4826ea408515d8ec74ca80 ---- ---- ---- JH636057.1
 ff7c4316cb69a8d571bd7ef85c1a10e4 ---- ---- ---- JH720455.1

This table indicates that while most contigs contain the same data, there are several with **sequence differences between the references**. Among those are **Chromosome 3**, **Chromosome Y**, and the **Mitochondrial Contig**.

Anecdotally the changes are for bases for which there was low confidence, with those low confidence bases masked out to be the `IUPAC` symbol for any base. However, _there does not seem to be a detailed comparison readily available (i.e. there's no proof that this is true)_.

Therefore, when doing comparisons across the four reference versions for each of these contigs, some care should be taken.

## Additional Information
Some further details can be found on this DNAnexus wiki page as of 2019/01/30.

Back to Top

<hr>
