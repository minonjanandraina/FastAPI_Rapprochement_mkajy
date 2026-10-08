## Reconciliation process flow

1. mainTango: Clean Tango files  and upload data to staging area splitted as: 
    * Normale transaction, 
    * manual rollback, 
    * auto rollback 
    * Manual Transfer (named manual transaction in the report)2
2. mainPICO: Clean pico Transaction and upload data to staging area PICO
3. mainOM: Clean OM Transaction and upload data to staging area OM (this is the last cleaned data from OM)
4. mainAMS: Get Transaction from clean data from DB BIC
5. generateOM_Transaction: This generate OM transaction with all details from PAMF to output/OM
6. generatePAMF_Transaction: This generate Front Transaction with all details from OM tou output/FRONT
7. 

