# ONGEZA modules

| Module | Path | Aina | Records | Columns | Sort | Filters | Create | Sek | Error |
|---|---|---|---|---|---|---|---|---|---|
| Worker > Tractor agents | `/crud/tractor-agent/tractoragents` | vue | 0 | 10 | 4 | 14 | /crud/tractor-agent/create-tractor-agent | 3.3 |  |
| Worker > Agents | `/crud/worker/agents?workeid=` | vue | 646 | 12 | 4 | 14 | /crud/worker/create-agent | 3.8 |  |
| Worker > Employees | `/crud/worker/employees?workeid=` | vue | 83 | 12 | 4 | 14 | /crud/worker/create-employee | 2.7 |  |
| Worker > Warehouses | `/crud/worker/warehouses?workeid=` | vue | 2 | 13 | 4 | 14 | /crud/worker/create-warehouse | 3.0 |  |
| Worker > Extended Stores | `/crud/worker/extended-stores` | table |  | 7 | 0 | 0 | /crud/worker/create-extended-store | 1.4 |  |
| Worker > Shops | `/crud/worker/shops?workeid=` | vue | 36 | 12 | 4 | 14 | /crud/worker/create-shop | 3.3 |  |
| Worker > Clusters | `/crud/clusters/index` | vue | 20 | 4 | 3 | 2 | /crud/clusters/create | 1.8 |  |
| Worker > All Workers | `/crud/worker/index?workeid=` | vue | 828 | 12 | 4 | 14 | /crud/worker/create2 | 2.7 |  |
| Worker > Worker phone | `/crud/workerphone/index2?workerid=` | vue | 1392 | 7 | 3 | 3 | /crud/workerphone/create2 | 1.9 |  |
| Worker > Worker leave type | `/crud/leavetype/index?workerid=` | table |  | 5 | 0 | 0 | /crud/leavetype/create | 9.4 |  |
| Worker > Worker leave | `/crud/workerleave/index?workerid=` | page |  | 0 | 0 | 0 |  | 8.6 | An internal server error occurred |
| Worker > Worker Linked | `/crud/workerlink/index` | table |  | 4 | 0 | 0 |  | 6.8 |  |
| Worker > Candidate Workers | `/survey/candidateworker/index` | grid | 1 | 8 | 6 | 7 | /survey/candidateworker/create | 4.2 |  |
| Worker > Worker Reports > Tickets Report | `/crud/ticket/ticketreport` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Worker > Worker Reports > Survey Report | `/survey/default/surveycallreport` | table |  | 4 | 0 | 0 |  | 5.4 |  |
| Worker > Worker Reports > New Customer Survey Report | `/survey/default/newcustomersurveyreport` | table |  | 5 | 0 | 0 |  | 16.2 |  |
| Org Structure > Position Wise | `/crud/organizationpositions/org-structure-positionwise` | page |  | 0 | 0 | 0 |  | 10.3 |  |
| Org Structure > Department Wise | `/crud/organizationpositions/org-structure-departmentwise` | page |  | 0 | 0 | 0 |  | 8.7 |  |
| Customer > All Customers | `/crud/customer/index2` | vue | 275468 | 11 | 3 | 9 | /crud/customer/create | 9.0 |  |
| Customer > Customer phone | `/crud/customerphone/index` | grid | 183295 | 7 | 6 | 7 | /crud/customerphone/create | 5.6 |  |
| Customer > Customer map | `/crud/customer/map?workerid=` | page |  | 0 | 0 | 0 |  | 6.0 |  |
| Sales > All Sales | `/crud/sale/index?workerid=` | vue | 194131 | 17 | 12 | 17 |  | 42.1 |  |
| Sales > Deleted Sales | `/crud/sale/deletedsale?workerid=` | grid |  | 15 | 8 | 13 |  | 11.0 |  |
| Sales > Sales Reports > Receipt Sales | `/crud/sale/receiptsale?workerid=` | grid | 190 | 18 | 7 | 12 |  | 29.0 |  |
| Sales > Sales Reports > Sales Per Month | `/crud/sale/salespermonth` | table |  | 2 | 0 | 0 |  | 4.1 |  |
| Sales > Sales Reports > Sales Per Item | `/crud/sale/salesperitem?workerid=` | page |  | 0 | 0 | 0 |  | 4.2 |  |
| Sales > Sales Reports > Sales Per Worker | `/crud/sale/saleperworker` | table |  | 35 | 0 | 0 |  | 47.5 |  |
| Sales > Sales Reports > Sales Per Area | `/report/default/salesperarea` | page |  | 0 | 0 | 0 |  | 7.9 | An internal server error occurred |
| Sales > Sale targets | `/crud/saletargets/index` | vue | 158 | 7 | 3 | 0 | /crud/saletargets/create | 1.9 |  |
| Stock > Profoma > Agrimachine Profoma | `/crud/agrimachine/profoma` | vue | 209 | 10 | 3 | 4 |  | 2.0 |  |
| Stock > Stock Dispatch > All stock dispatch | `/crud/stockdispatch/index` | vue | 360 | 12 | 1 | 7 | /crud/stockdispatch/create | 1.7 |  |
| Stock > Stock Dispatch > Stock Requests | `/crud/stockdispatch/requests` | vue | 135 | 7 | 2 | 4 |  | 1.8 |  |
| Stock > Stock Dispatch > all stock deliveries | `/crud/stockdispatch/deliveries` | vue | 104 | 10 | 4 | 7 | /crud/stockdispatch/create | 1.8 |  |
| Stock > Agrimachinery > All Agrimachines | `/crud/agrimachine/index` | vue | 510 | 17 | 3 | 8 | /crud/agrimachine/create | 2.1 |  |
| Stock > Agrimachinery > Agrimachine Activity | `/crud/agrimachine/agrimachinelog` | vue | 1165 | 14 | 3 | 2 |  | 1.9 |  |
| Stock > Agrimachinery > Pending Agrimachines | `/crud/agrimachine/pendingagrimachine` | vue | 0 | 12 | 3 | 4 |  | 1.8 |  |
| Stock > O/C Stock > O/C Stock | `/crud/stockactivity/ocstock?workerid` | table |  | 6 | 0 | 0 |  | 6.7 |  |
| Stock > O/C Stock > O/C HQ Stock | `/crud/stockactivity/hqocstock` | page |  | 0 | 0 | 0 |  | 30.8 | An internal server error occurred |
| Stock > Issue Stock | `/crud/stock/issue?workerid=` | table |  | 5 | 0 | 0 |  | 2.0 |  |
| Stock > Return Stock | `/crud/stock/returnstock?workerid=` | page |  | 0 | 0 | 0 |  | 7.5 |  |
| Stock > Stocks > Payg Stocks | `/crud/stock/paygstock` | table |  | 2 | 0 | 0 |  | 7.7 |  |
| Stock > Stocks > Crud > Paygstockactivity > Stocksummary | `/crud/paygstockactivity/stocksummary` | table |  | 2 | 0 | 0 |  | 19.2 |  |
| Stock > Stocks > All Stocks | `/crud/stock/index2?workerid=` | vue | 16337 | 11 | 5 | 6 | /crud/stock/createongezastock | 3.2 |  |
| Stock > Stocks > Pending Stocks | `/crud/stock/pending?workerid=` | page |  | 0 | 0 | 0 |  | 4.6 |  |
| Stock > Activity Reports > Crud > Paygstockactivity > Index | `/crud/paygstockactivity/index` | grid | 115548 | 10 | 10 | 10 |  | 5.1 |  |
| Stock > Activity Reports > Stock Activity | `/crud/stockactivity/index?workerid=` | grid | 61 | 17 | 12 | 11 | /crud/stockactivity/create | 36.5 |  |
| Stock > Activity Reports > Full Stock Activity | `/crud/stockactivity/indexall?workerid=` | grid | 785 | 17 | 12 | 11 | /crud/stockactivity/create | 35.1 |  |
| Stock > Stock Anomaly | `/crud/stock/stockanomaly` | grid | 639 | 13 | 8 | 9 |  | 65.0 |  |
| Stock > Stock Reports > Stock Report | `/crud/stock/stockreports?workerid=` | page |  | 0 | 0 | 0 |  | 56.0 | An internal server error occurred |
| Stock > Stock Reports > Stock Summary Report | `/crud/stock/summaryreport?workerid=` | page |  | 0 | 0 | 0 |  | 57.3 | Integrity constraint violation |
| Stock > Audit > Perform Audit | `/report/audit/performaudit` | page |  | 0 | 0 | 0 |  | 4.2 |  |
| Stock > Audit > All Audits | `/report/audit/auditplatform` | page |  | 0 | 0 | 0 |  | 10.3 | An internal server error occurred |
| Stock > Audit > Debtbook | `/crud/debtbook/index` | grid |  | 11 | 5 | 7 | /crud/debtbook/create | 6.9 | An internal server error occurred |
| Stock > Audit > Audit Report | `/report/audit/auditreport` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Stock > Audit > Audit Map | `/report/auditgps/map` | page |  | 0 | 0 | 0 |  | 6.7 |  |
| Stock > Items > All Items | `/crud/item/index2?workerid=` | vue | 1082 | 8 | 3 | 6 | /crud/item/create2 | 1.9 |  |
| Stock > Items > Item Price History | `/crud/itempricehistory/index?workerid=` | grid | 595 | 5 | 5 | 5 | /crud/itempricehistory/create | 7.9 | An internal server error occurred |
| Stock > Items > Item Categories | `/crud/itemcategory/index` | vue | 11 | 7 | 3 | 2 | /crud/itemcategory/create2 | 2.0 |  |
| Stock > Item Pricing > Pricing Histry | `/crud/itempricinglogs/indexall` | vue | 85357 | 10 | 2 | 4 |  | 3.2 |  |
| Stock > Item Pricing > Current Pricing | `/crud/itempricing/index` | vue | 47181 | 8 | 2 | 4 | /crud/itempricing/create | 2.2 |  |
| Stock > Supplier > All Suppliers | `/crud/supplier/index2` | vue | 20 | 5 | 0 | 3 | /crud/supplier/create | 1.7 |  |
| Stock > Supplier > Pending Supplier Stock | `/crud/stock/stockapproval2` | vue |  | 8 | 0 | 0 |  | 1.5 |  |
| Stock > Supplier > Supplier Log | `/crud/supplierlog/index2` | vue | 4588 | 7 | 3 | 4 |  | 1.9 |  |
| Stock > Retail Orders > Warehouse Stock Availability | `/crud/stock/warehousestockavailability` | vue |  | 4 | 0 | 0 |  | 2.6 |  |
| Stock > Retail Orders > All Stock Requests | `/crud/stock/retailrequests` | page |  | 0 | 0 | 0 |  | 4.0 | An internal server error occurred |
| Stock > Retail Orders > Request Stock | `/crud/stock/createretailstockrequest` | table |  | 4 | 0 | 0 |  | 2.7 |  |
| Stock > Stock Status | `/crud/stock/stockstatus` | vue |  | 7 | 0 | 0 |  | 40.7 |  |
| Stock > Exchange Stock | `/crud/stock/exchangestock` | page |  | 0 | 0 | 0 |  | 2.3 |  |
| Payg > All Devices | `/payg/paygdevice/index` | grid | 36585 | 19 | 13 | 13 | /payg/paygdevice/create | 5.9 |  |
| Payg > Defaulters > Payg Defaulters | `/payg/paygdevice/defaultersportal` | table |  | 16 | 0 | 0 |  | 24.4 |  |
| Payg > Defaulters > Credit Defaulters | `/payg/paygdevice/paygcreditportal` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Payg > Sales Performance > Agents Performance | `/payg/paygdevice/sosalesreport` | table |  | 19 | 0 | 0 |  | 37.2 |  |
| Payg > Sales Performance > TL Performance | `/payg/paygdevice/tlsalesreport` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Payg > Sales Performance > District Performance | `/payg/paygdevice/districtsalesreport` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Payg > Payg Credits > All Credits | `/payg/paygcredit/index` | grid | 79 | 10 | 10 | 10 |  | 5.8 |  |
| Payg > Payg Credits > Credit Eligibles | `/payg/paygdevice/creditcustomers` | table |  | 11 | 0 | 0 |  | 46.3 |  |
| Payg > Payg Token | `/payg/paygtoken/index` | grid | 114 | 10 | 10 | 9 |  | 15.4 |  |
| Payg > Payg Token Payment | `/payg/paygtokenpayment/index` | grid | 111 | 11 | 10 | 10 |  | 15.2 |  |
| Payg > Payg Reports > Outstanding Report | `/payg/paygdevice/outstandingreport` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Payg > Payg Reports > Sales Summary | `/payg/paygdevice/paygsalessummary` | table |  | 15 | 0 | 0 |  | 7.0 |  |
| Payg > Payg Reports > Device Report | `/payg/paygdevice/paygdevicereport` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Payg > Payg Reports > Repossession Report | `/payg/paygdevice/repossessionreport` | table |  | 16 | 0 | 0 |  | 12.5 |  |
| Payg > Payg Reports > Replacement Report | `/payg/paygdevice/replacementreport` | page |  | 0 | 0 | 0 |  | 19.4 | An internal server error occurred |
| Payg > Payg Reports > Repossession Summary | `/payg/paygdevice/reposessionreport` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Payg > Payg Reports > Device Summary | `/payg/paygdevice/paygdevicesummary` | page |  | 0 | 0 | 0 |  | 39.9 | An internal server error occurred |
| Payg > Payg Reports > Payg Charts | `/payg/paygreportlog/chartsportal` | page |  | 0 | 0 | 0 |  | 139.4 |  |
| Finance > Upload Excel File | `/crud/uploadfile` | page |  | 0 | 0 | 0 |  | 2.3 |  |
| Finance > E-Money > All E-Money | `/crud/payment/index2` | vue | 3015237 | 16 | 2 | 10 | /crud/payment/createpaymentwithinterface | 6.6 |  |
| Finance > E-Money > E-Money Log | `/crud/paymentlog/index?workerid=` | grid | 56324 | 7 | 5 | 4 | /crud/paymentlog/create | 10.4 |  |
| Finance > E-Money > NMB | `/crud/nmb/index` | vue | 70324 | 8 | 0 | 5 |  | 2.2 |  |
| Finance > E-Money > Reversed Payment | `/crud/reversepayments/index` | vue | 19 | 13 | 2 | 10 |  | 1.8 |  |
| Finance > Manual Payments > All Manual Payments | `/crud/payment/manual` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Finance > Manual Payments > Pending Payments | `/crud/payment/approvepayment` | grid |  | 11 | 9 | 0 |  | 6.7 |  |
| Finance > Manual Payments > Confirmed Payments | `/crud/confirmedpayment/index` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Finance > Service Payments > Invalid Payments | `/payg/paygtokenpayment/invaliddeposit2` | vue | 1111 | 9 | 2 | 5 |  | 44.2 |  |
| Finance > Service Payments > Unassigned TokenPayment | `/payg/paygtokenpayment/unassigned2` | vue | 4815 | 9 | 2 | 6 |  | 41.6 |  |
| Finance > Service Payments > No-Sale Payments | `/payg/paygtokenpayment/nosale2` | vue | 778 | 9 | 2 | 5 |  | 39.5 |  |
| Finance > Service Payments > Unassigned Payments | `/crud/payment/unassigned2` | vue | 4278 | 9 | 2 | 5 |  | 39.1 |  |
| Finance > Service Payments > Order Payments | `/crud/payment/orderpayments2` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Finance > Budget > Create Budget | `/payroll/budgetexpenses/createbudget` | page |  | 0 | 0 | 0 |  | 2.1 |  |
| Finance > Budget > Budget Approximate | `/payroll/budgetexpenses/index2` | vue | 42 | 15 | 2 | 2 | /payroll/budgetexpenses/createbudget | 2.6 |  |
| Finance > Budget > Budget Approval | `/payroll/budgetexpenses/indexadmin2` | vue | 6802 | 14 | 2 | 6 |  | 2.8 |  |
| Finance > Budget > Budget Return | `/payroll/budgetexpenses/indexreturn2` | vue | 74 | 14 | 0 | 3 |  | 2.4 |  |
| Finance > Budget > Sales Point Budget | `/payroll/retailbudget/index` | vue | 0 | 17 | 0 | 2 | /payroll/retailbudget/create | 1.7 |  |
| Finance > Budget > Budget Summary | `/payroll/budgetexpenses/indexsummary2` | page |  | 0 | 0 | 0 |  | 9.0 |  |
| Finance > Budget > Non-Budget Expenses | `/payroll/budgetexpenses/indexnonbudget` | grid | 5 | 5 | 5 | 5 |  | 11.7 |  |
| Finance > Finance Reports > Outstanding Balance | `/report/default/outstandingbalance?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Finance > Finance Reports > Payments Per Provider | `/crud/payment/provider` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Finance > Finance Reports > Cash Collected | `/crud/sale/cashcollected?workerid=` | table |  | 2 | 0 | 0 |  | 27.4 |  |
| Finance > Finance Reports > Profit & Loss Report | `/payroll/budgetexpenses/indexprofitloss` | page |  | 0 | 0 | 0 |  | 90.1 | Page load timeout (>90s) |
| Finance > Finance Reports > Annual Report | `/payroll/budgetexpenses/annualreport` | page |  | 0 | 0 | 0 |  | 7.3 | An internal server error occurred |
| Finance > Payroll > Defaulter snapshots | `/payroll/workerbehavioragent/defaulterssnapshots` | vue | 5919 | 10 | 2 | 2 |  | 2.2 |  |
| Finance > Payroll > Worker Monthly Commission | `/payroll/workerbehavioragent/workermonthlycommission` | vue |  | 18 | 2 | 6 |  | 2.6 |  |
| Finance > Payroll > Worker Transport Allowances | `/payroll/workerbehavioragent/workerweeklytransportallowances` | vue |  | 16 | 4 | 6 |  | 2.0 |  |
| Finance > Payroll > Agents Payroll | `/payroll/workerbehavioragent/index` | grid | 644 | 19 | 0 | 0 |  | 27.7 |  |
| Finance > Payroll > Transport Allowances | `/crud/worker/workertransportallowances` | grid |  | 14 | 13 | 0 |  | 8.1 |  |
| Finance > Payroll > Fully Paid Bonus | `/payg/paygdevice/sobonusreport` | page |  | 0 | 0 | 0 |  | 60.9 | 504 Gateway Time-out |
| Finance > Payroll > Worker deduction | `/payg/paygdevice/workerdeductions` | page |  | 0 | 0 | 0 |  | 8.6 |  |
| Finance > Solar reconciliation | `/payg/paygtokenpayment/solarreconciliation` | page |  | 0 | 0 | 0 |  | 6.9 |  |
| Audit > All Audits | `/crud/auditreview/index` | vue | 514 | 9 | 3 | 5 |  | 2.1 |  |
| Zones > District | `/crud/district/index?workerid=` | grid | 152 | 7 | 6 | 7 | /crud/district/create | 14.9 |  |
| Zones > Ward | `/crud/ward/index?workerid=` | table |  | 5 | 0 | 0 | /crud/ward/create | 7.5 |  |
| Zones > Village | `/crud/village/index?workerid=` | table |  | 4 | 0 | 0 | /crud/village/create | 8.9 |  |
| Zones > Warehouse | `/crud/warehouse/index?workerid=` | table |  | 6 | 0 | 0 | /crud/warehouse/create | 8.3 |  |
| Tickets 0 > My Tickets | `/crud/ticket/index` | grid |  | 12 | 12 | 12 | /crud/ticket/create | 13.5 |  |
| Tickets 0 > All Tickets | `/crud/ticket/indexall` | grid | 2469702 | 11 | 11 | 11 |  | 14.7 |  |
| Sms > Inbox | `/sms/inbox/index` | grid |  | 7 | 7 | 6 | /sms/inbox/create | 10.3 |  |
| Sms > Outbox | `/sms/outbox/index` | grid | 3 | 7 | 7 | 6 | /sms/outbox/create | 10.3 |  |
| Sms > Sent SMS | `/sms/sentsms/index` | grid |  | 6 | 6 | 6 |  | 8.1 |  |
| Sms > Bulk SMS > SMS Workers | `/sms/outbox/smsworkers` | page |  | 0 | 0 | 0 |  | 8.2 |  |
| Sms > Bulk SMS > SMS TLs | `/sms/outbox/smstls` | page |  | 0 | 0 | 0 |  | 7.8 |  |
| Sms > Bulk SMS > SMS Customer | `/sms/outbox/smscustomers` | page |  | 0 | 0 | 0 |  | 7.8 |  |
| Sms > Bulk SMS > Bulk Groups | `/sms/bulkgroup/index` | grid | 1 | 2 | 2 | 2 | /sms/bulkgroup/create | 6.4 |  |
| Sms > Bulk SMS > Import SMS | `/sms/outbox/upload` | page |  | 0 | 0 | 0 |  | 1.7 |  |
| Sms > Bulk SMS > GCM SMS | `/sms/default/gcm` | page |  | 0 | 0 | 0 |  | 6.4 |  |
| Sms > Contacts > All Contacts | `/sms/contact/index` | grid | 1 | 4 | 3 | 4 | /sms/contact/create | 6.4 |  |
| Sms > Contacts > Import Contacts | `/sms/contact/upload` | page |  | 0 | 0 | 0 |  | 6.2 |  |
| Sms > Settings > SMS Category | `/sms/smscategory/index` | grid | 106 | 2 | 2 | 2 | /sms/smscategory/create | 6.4 |  |
| Sms > Settings > SMS Template | `/sms/template/index` | grid | 148 | 3 | 3 | 3 | /sms/template/create | 6.5 |  |
| Sms > Settings > SMS Senders | `/sms/sms-sender/index` | vue | 0 | 4 | 2 | 4 | /sms/sms-sender/create | 1.7 |  |
| Sms > Notification | `/sms/workernotification/index` | grid | 3 | 8 | 8 | 8 | /sms/workernotification/create | 6.1 |  |
| Sms > SMS Reports > SMS Summary | `/sms/default/index` | table |  | 2 | 0 | 0 |  | 6.4 |  |
| Sms > SMS Reports > SMS Operators | `/sms/default/operator` | table |  | 19 | 0 | 0 |  | 29.1 |  |
| Survey > Payg Survey | `/survey/default/solar?start_exit=1` | page |  | 0 | 0 | 0 |  | 2.0 |  |
| Survey > Remainder Survey | `/survey/default/survey?start_exit=1&categories=17` | table |  | 3 | 0 | 0 |  | 21.8 |  |
| Survey > Worker Survey | `/survey/candidateworker/surveycandidate?start_exit=1` | page |  | 0 | 0 | 0 |  | 6.8 |  |
| Config > Manage Positions | `/menu/positions` | table |  | 8 | 0 | 0 |  | 2.9 |  |
| Config > Users | `/users/index2` | vue | 83 | 10 | 3 | 4 | /users/create2 | 2.0 |  |
| Config > Roles | `/role/index` | table |  | 5 | 0 | 0 | /role/create | 5.7 |  |
| Config > Permission | `/permission/index2` | vue | 1122 | 4 | 2 | 1 | /permission/create | 1.8 |  |
| Config > Manage Menus | `/menu/index` | vue |  | 11 | 0 | 0 | /menu/create | 1.8 |  |
| Config > Permission Group | `/permissiongroup/index2` | vue | 36 | 4 | 2 | 1 | /permissiongroup/create | 1.8 |  |
| Config > Value List | `/crud/valuelist/index2` | page |  | 0 | 0 | 0 |  | 7.8 | An internal server error occurred |
| Config > survey > Survey Data | `/survey/surveydata/index` | grid | 3875904 | 6 | 5 | 6 | /survey/surveydata/create | 43.9 |  |
| Config > survey > Survey Question | `/survey/surveyquestion/index` | table |  | 10 | 0 | 0 | /survey/surveyquestion/create | 9.0 |  |
| Config > survey > Survey Category | `/survey/surveycategory/index` | table |  | 3 | 0 | 0 | /survey/surveycategory/create | 6.8 |  |
| Config > survey > Survey Valuelist | `/survey/surveyvaluelist/index` | table |  | 6 | 0 | 0 | /survey/surveyvaluelist/create | 5.9 |  |
| Config > Administration > Notifications Config | `/crud/notificationconfig/index` | vue | 1 | 7 | 3 | 5 | /crud/notificationconfig/create | 2.0 |  |
| Config > Administration > Notification Type | `/crud/notificationtype/index` | vue | 27 | 3 | 3 | 2 | /crud/notificationtype/create | 2.2 |  |
| Config > Administration > Farmer group Order status | `/crud/farmergrouporderstatus/index` | vue | 5 | 3 | 3 | 2 | /crud/farmergrouporderstatus/create | 1.7 |  |
| Config > Administration > Purchase category | `/crud/purchaserequestcategory/index` | vue | 6 | 4 | 3 | 2 | /crud/purchaserequestcategory/create | 1.6 |  |
| Config > Administration > Department | `/crud/department/index` | page |  | 0 | 0 | 0 |  | 1.7 |  |
| Config > Administration > Organization Position | `/crud/organizationpositions/index` | vue | 37 | 7 | 3 | 3 | /crud/organizationpositions/create | 1.7 |  |
| Config > Administration > Vendors > All Vendor | `/crud/vendors/index` | vue | 0 | 6 | 3 | 2 | /crud/vendors/create | 1.7 |  |
| Config > Administration > Vendors > Vendor request Category | `/crud/vendorsrequestcategory/index` | vue | 0 | 5 | 3 | 2 | /crud/vendorsrequestcategory/create | 1.6 |  |
| Apps > Device Info | `/crud/deviceinfo/index` | table |  | 8 | 0 | 0 | /crud/deviceinfo/create | 5.8 |  |
| Apps > API Hit Log | `/crud/apihitlog/index` | grid |  | 6 | 5 | 5 | /crud/apihitlog/create | 5.5 |  |
| Apps > Sync Log | `/crud/synclog/index` | table |  | 6 | 0 | 0 | /crud/synclog/create | 10.0 |  |
| Apps > Complete Sync | `/crud/completesync/index` | table |  | 6 | 0 | 0 | /crud/completesync/create | 10.0 |  |
| Customer Service > Service Page | `/customerservice/index` | page |  | 0 | 0 | 0 |  | 1.6 |  |
| Customer Service > Shops Info | `/customerservice/shopsinfo` | vue | 6048 | 7 | 0 | 4 |  | 3.3 |  |
| Reports | `/reports` | page |  | 0 | 0 | 0 |  | 1.8 |  |
| Assets > All Assets | `/crud/asset/index` | vue | 20 | 11 | 3 | 8 | /crud/asset/create | 2.1 |  |
| Assets > Asset Names | `/crud/assetnames/index` | vue | 14 | 3 | 3 | 2 | /crud/assetnames/create | 1.6 |  |
| Purchase Request | `/crud/purchaserequest/index` | vue | 0 | 9 | 3 | 5 | /crud/purchaserequest/create | 1.8 |  |
