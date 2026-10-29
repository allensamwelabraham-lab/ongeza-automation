# ONGEZA modules

| Module | Path | Aina | Records | Columns | Sort | Filters | Create | Sek | Error |
|---|---|---|---|---|---|---|---|---|---|
| Agro > Stockist Machinery Orders | `/crud/stockistorder/indexall` | vue | 207 | 17 | 4 | 8 |  | 3.9 |  |
| Agro > Stockist Loans | `/crud/stockistloan/index` | vue | 123 | 11 | 2 | 2 | /crud/stockistloan/create | 3.8 |  |
| Agro > Stockist Credit Order | `/crud/stockistorder/index` | vue | 113 | 16 | 4 | 8 |  | 4.1 |  |
| Agro > Credit Order Timeline | `/crud/stockistorder/credit-timeline` | vue | 1 | 8 | 0 | 5 |  | 12.8 |  |
| Agro > Customer Orders > All Orders | `/crud/customerorder/index?workerid=` | vue | 123871 | 14 | 5 | 12 |  | 6.5 |  |
| Agro > Customer Orders > Paid Orders | `/crud/customerorder/paidcustomerorder?workerid=` | grid | 51 | 9 | 7 | 7 |  | 20.7 |  |
| Worker > Tractor agents | `/crud/tractor-agent/tractoragents` | vue | 0 | 10 | 4 | 14 | /crud/tractor-agent/create-tractor-agent | 12.6 |  |
| Worker > Agents | `/crud/worker/agents?workeid=` | vue | 646 | 12 | 4 | 14 | /crud/worker/create-agent | 10.8 |  |
| Worker > Employees | `/crud/worker/employees?workeid=` | vue | 148 | 12 | 4 | 14 | /crud/worker/create-employee | 10.5 |  |
| Worker > Warehouses | `/crud/worker/warehouses?workeid=` | vue | 34 | 13 | 4 | 14 | /crud/worker/create-warehouse | 3.2 |  |
| Worker > Shops | `/crud/worker/shops?workeid=` | vue | 29 | 12 | 4 | 14 | /crud/worker/create-shop | 2.9 |  |
| Worker > Clusters | `/crud/clusters/index` | vue | 20 | 4 | 3 | 2 | /crud/clusters/create | 1.6 |  |
| Worker > All Workers | `/crud/worker/index?workeid=` | vue | 987 | 12 | 4 | 14 | /crud/worker/create2 | 2.8 |  |
| Worker > Worker phone | `/crud/workerphone/index2?workerid=` | vue | 1412 | 7 | 3 | 3 | modal | 1.7 |  |
| Worker > Worker leave type | `/crud/leavetype/index?workerid=` | table |  | 5 | 0 | 0 | /crud/leavetype/create | 12.7 |  |
| Worker > Worker leave | `/crud/workerleave/index?workerid=` | page |  | 0 | 0 | 0 |  | 24.4 |  |
| Worker > Worker Linked | `/crud/workerlink/index` | table |  | 4 | 0 | 0 |  | 34.6 |  |
| Worker > Candidate Workers | `/survey/candidateworker/index` | grid | 232 | 8 | 6 | 7 | /survey/candidateworker/create | 41.4 |  |
| Worker > Worker Reports > Tickets Report | `/crud/ticket/ticketreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Worker > Worker Reports > Survey Report | `/survey/default/surveycallreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Worker > Worker Reports > New Customer Survey Report | `/survey/default/newcustomersurveyreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Org Structure > Position Wise | `/crud/organizationpositions/org-structure-positionwise` |  |  | 0 | 0 | 0 |  |  | inspect failed: ReadTimeoutError: HTTPConnectionPool(host='localhost', port=53965): Read timed out. (read timeout=120) |
| Org Structure > Department Wise | `/crud/organizationpositions/org-structure-departmentwise` | page |  | 0 | 0 | 0 |  | 110.3 |  |
| Customer > All Customers | `/crud/customer/index2` | vue | 274916 | 11 | 3 | 9 | /crud/customer/create | 12.9 |  |
| Customer > Customer phone | `/crud/customerphone/index` | grid | 182742 | 7 | 6 | 7 | /crud/customerphone/create | 29.1 |  |
| Customer > Customer map | `/crud/customer/map?workerid=` | page |  | 0 | 0 | 0 |  | 47.3 |  |
| Sales > All Sales | `/crud/sale/index?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sales > Deleted Sales | `/crud/sale/deletedsale?workerid=` |  |  | 0 | 0 | 0 |  |  | inspect failed: ReadTimeoutError: HTTPConnectionPool(host='localhost', port=53965): Read timed out. (read timeout=120) |
| Sales > Sales Reports > Receipt Sales | `/crud/sale/receiptsale?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sales > Sales Reports > Sales Per Month | `/crud/sale/salespermonth` | table |  | 2 | 0 | 0 |  | 59.8 |  |
| Sales > Sales Reports > Sales Per Item | `/crud/sale/salesperitem?workerid=` | page |  | 0 | 0 | 0 |  | 51.1 |  |
| Sales > Sales Reports > Sales Per Worker | `/crud/sale/saleperworker` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sales > Sales Reports > Sales Per Area | `/report/default/salesperarea` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sales > Sale targets | `/crud/saletargets/index` | vue | 158 | 7 | 3 | 0 | modal | 52.2 |  |
| Stock > Agrimachinery > All Agrimachines | `/crud/agrimachine/index` | vue | 510 | 17 | 3 | 8 | /crud/agrimachine/create | 38.6 |  |
| Stock > Agrimachinery > Agrimachine Activity | `/crud/agrimachine/agrimachinelog` | vue | 2073 | 14 | 3 | 2 |  | 33.3 |  |
| Stock > Agrimachinery > Pending Agrimachines | `/crud/agrimachine/pendingagrimachine` | vue | 0 | 12 | 3 | 4 |  | 19.4 |  |
| Stock > Agrimachinery > Agrimachine Profoma | `/crud/agrimachine/profoma` | vue | 154 | 9 | 3 | 3 | /crud/agrimachine/createprofoma | 3.3 |  |
| Stock > Stock Dispatch > All stock dispatch | `/crud/stockdispatch/index` | vue | 184 | 12 | 1 | 7 | /crud/stockdispatch/create | 2.8 |  |
| Stock > Stock Dispatch > Stock Requests | `/crud/stockdispatch/requests` | vue | 122 | 7 | 2 | 4 |  | 1.6 |  |
| Stock > Stock Dispatch > all stock deliveries | `/crud/stockdispatch/deliveries` | vue | 183 | 10 | 4 | 7 | /crud/stockdispatch/create | 2.0 |  |
| Stock > Issue Stock | `/crud/stock/issue?workerid=` | table |  | 5 | 0 | 0 |  | 1.6 |  |
| Stock > Return Stock | `/crud/stock/returnstock?workerid=` | page |  | 0 | 0 | 0 |  | 12.0 |  |
| Stock > Stocks > All Stocks | `/crud/stock/index2?workerid=` | vue | 16097 | 11 | 5 | 6 | /crud/stock/createongezastock | 12.2 |  |
| Stock > Stocks > Payg Stocks | `/crud/stock/paygstock` | table |  | 2 | 0 | 0 |  | 22.7 |  |
| Stock > Stocks > OS-300 Stock | `/crud/paygstockactivity/stocksummary` | table |  | 2 | 0 | 0 |  | 37.9 |  |
| Stock > Stocks > Pending Stocks | `/crud/stock/pending?workerid=` | page |  | 0 | 0 | 0 |  | 39.3 |  |
| Stock > O/C Stock > O/C Stock | `/crud/stockactivity/ocstock?workerid` | table |  | 6 | 0 | 0 |  | 40.1 |  |
| Stock > O/C Stock > O/C HQ Stock | `/crud/stockactivity/hqocstock` | page |  | 0 | 0 | 0 |  | 58.7 |  |
| Stock > Activity Reports > Stock Activity | `/crud/stockactivity/index?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Activity Reports > Full Stock Activity | `/crud/stockactivity/indexall?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Activity Reports > OS-300 Activity | `/crud/paygstockactivity/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Stock Anomaly | `/crud/stock/stockanomaly` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Stock Reports > Stock Report | `/crud/stock/stockreports?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Stock Reports > Stock Summary Report | `/crud/stock/summaryreport?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Audit > Perform Audit | `/report/audit/performaudit` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Audit > All Audits | `/report/audit/auditplatform` | page |  | 0 | 0 | 0 |  | 39.0 |  |
| Stock > Audit > Debtbook | `/crud/debtbook/index` | grid |  | 11 | 5 | 7 | /crud/debtbook/create | 37.0 |  |
| Stock > Audit > Audit Report | `/report/audit/auditreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Audit > Audit Map | `/report/auditgps/map` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Items > All Items | `/crud/item/index2?workerid=` | vue | 1079 | 8 | 3 | 6 | /crud/item/create2 | 49.7 |  |
| Stock > Items > Item Price History | `/crud/itempricehistory/index?workerid=` | grid | 753 | 5 | 5 | 5 | /crud/itempricehistory/create | 81.4 |  |
| Stock > Items > Item Categories | `/crud/itemcategory/index` | vue | 10 | 7 | 3 | 2 | /crud/itemcategory/create2 | 50.7 |  |
| Stock > Items > Item Bundles | `/crud/itembundle/index?workerid=` | grid | 18 | 8 | 8 | 8 | /crud/itembundle/create | 48.9 |  |
| Stock > Item Pricing > Pricing Histry | `/crud/itempricinglogs/indexall` | vue | 85214 | 10 | 2 | 4 |  | 20.3 |  |
| Stock > Item Pricing > Current Pricing | `/crud/itempricing/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Supplier > All Suppliers | `/crud/supplier/index2` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Stock > Supplier > Pending Supplier Stock | `/crud/stock/stockapproval2` | vue |  | 8 | 0 | 0 |  | 15.6 |  |
| Stock > Supplier > Supplier Log | `/crud/supplierlog/index2` | vue | 7446 | 7 | 3 | 4 |  | 7.4 |  |
| Stock > Retail Orders > Warehouse Stock Availability | `/crud/stock/warehousestockavailability` | vue |  | 4 | 0 | 0 |  | 7.5 |  |
| Stock > Retail Orders > All Stock Requests | `/crud/stock/retailrequests` | page |  | 0 | 0 | 0 |  | 18.2 |  |
| Stock > Retail Orders > Request Stock | `/crud/stock/createretailstockrequest` | table |  | 4 | 0 | 0 |  | 23.0 |  |
| Stock > Stock Status | `/crud/stock/stockstatus` | vue |  | 6 | 0 | 0 |  | 22.9 |  |
| Stock > Exchange Stock | `/crud/stock/exchangestock` | page |  | 0 | 0 | 0 |  | 20.7 |  |
| Payg > All Devices | `/payg/paygdevice/index` | grid | 36584 | 19 | 13 | 13 | /payg/paygdevice/create | 19.7 |  |
| Payg > Defaulters > Payg Defaulters | `/payg/paygdevice/defaultersportal` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Defaulters > Credit Defaulters | `/payg/paygdevice/paygcreditportal` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Credits > All Credits | `/payg/paygcredit/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Credits > Credit Eligibles | `/payg/paygdevice/creditcustomers` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Token | `/payg/paygtoken/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Token Payment | `/payg/paygtokenpayment/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Sales Performance > Agents Performance | `/payg/paygdevice/sosalesreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Sales Performance > TL Performance | `/payg/paygdevice/tlsalesreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Sales Performance > District Performance | `/payg/paygdevice/districtsalesreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Reports > Device Report | `/payg/paygdevice/paygdevicereport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Reports > Outstanding Report | `/payg/paygdevice/outstandingreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Reports > Repossession Report | `/payg/paygdevice/repossessionreport` | table |  | 16 | 0 | 0 |  | 25.7 |  |
| Payg > Payg Reports > Replacement Report | `/payg/paygdevice/replacementreport` | page |  | 0 | 0 | 0 |  | 38.7 |  |
| Payg > Payg Reports > Repossession Summary | `/payg/paygdevice/reposessionreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Reports > Sales Summary | `/payg/paygdevice/paygsalessummary` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Reports > Device Summary | `/payg/paygdevice/paygdevicesummary` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Payg > Payg Reports > Payg Charts | `/payg/paygreportlog/chartsportal` | page |  | 0 | 0 | 0 |  | 177.0 |  |
| Agro > Franchise LPO | `/crud/lpoorder/index` | vue | 527 | 12 | 3 | 4 |  | 38.6 |  |
| Agro > Wholesale > Stockist > All stockist | `/crud/ongezastockist/index2` | vue | 3046 | 8 | 3 | 5 | /crud/ongezastockist/create2 | 30.0 |  |
| Agro > Wholesale > Stockist > Stockist Report | `/crud/ongezastockist/salesreport` | page |  | 0 | 0 | 0 |  | 27.1 |  |
| Agro > Wholesale > Wholesale Reports > Agro Wholesale Summary | `/report/default/agrowholesalesummary?itemtype=2&category=2` | page |  | 0 | 0 | 0 |  | 24.5 |  |
| Agro > Retail > Farmer Groups > Group Villages | `/crud/farmergroupvillage/index` | vue | 19 | 4 | 3 | 3 | /crud/farmergroupvillage/create | 12.6 |  |
| Agro > Retail > Farmer Groups > All Farmer Groups | `/crud/farmergroups/index` | vue | 37 | 9 | 3 | 6 | /crud/farmergroups/create | 2.1 |  |
| Agro > Retail > Farmer Groups > Group Orders | `/crud/farmergrouporder/index` | vue | 39 | 14 | 3 | 3 | modal | 2.1 |  |
| Agro > Retail > Retail Reports > Agro Retail Summary | `/report/default/agroretailsummary?itemtype=2&category=1` | page |  | 0 | 0 | 0 |  | 12.5 |  |
| Agro > Agro Reports > Seed Reports > Seed Summary | `/report/default/seedsummary` | page |  | 0 | 0 | 0 |  | 24.6 |  |
| Agro > Agro Reports > Seed Reports > Seed Cumulative Report | `/crud/sale/seedcullativereport` | page |  | 0 | 0 | 0 |  | 39.3 |  |
| Agro > Agro Reports > Seed Reports > Seed Sales Per District Chart | `/crud/sale/seedsalesperdistrictchart` | page |  | 0 | 0 | 0 |  | 44.8 |  |
| Agro > Agro Reports > Seed Reports > Yearly Cumulative Seed Sales Report | `/crud/sale/yearlycumulativeseedsalesreport` | page |  | 0 | 0 | 0 |  | 42.5 |  |
| Agro > Agro Reports > Fertilizer Reports > District Fertilizer Summary | `/report/default/districtfertilizersummary` | page |  | 0 | 0 | 0 |  | 39.9 |  |
| Agro > Agro Reports > Fertilizer Reports > Farmer-Group Fertilizer Summary | `/crud/farmergroup/fertilizerreport` | page |  | 0 | 0 | 0 |  | 36.2 |  |
| Agro > Agro Reports > Sales Map report | `/crud/sale/mapreport` | page |  | 0 | 0 | 0 |  | 39.9 |  |
| Finance > Upload Excel File | `/crud/uploadfile` | page |  | 0 | 0 | 0 |  | 25.6 |  |
| Finance > E-Money > All E-Money | `/crud/payment/index2` | vue | 3101662 | 16 | 2 | 10 | /crud/payment/createpaymentwithinterface | 35.6 |  |
| Finance > E-Money > E-Money Log | `/crud/paymentlog/index?workerid=` | grid | 57912 | 7 | 5 | 4 | /crud/paymentlog/create | 64.8 |  |
| Finance > E-Money > NMB | `/crud/nmb/index` | grid | 68906 | 9 | 7 | 5 |  | 39.2 |  |
| Finance > E-Money > Reversed Payment | `/crud/reversepayments/index` | vue | 19 | 13 | 2 | 10 |  | 37.7 |  |
| Finance > Manual Payments > All Manual Payments | `/crud/payment/manual` | page |  | 0 | 0 | 0 |  | 61.2 |  |
| Finance > Manual Payments > Pending Payments | `/crud/payment/approvepayment` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Manual Payments > Confirmed Payments | `/crud/confirmedpayment/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Service Payments > Invalid Payments | `/payg/paygtokenpayment/invaliddeposit2` | vue | 1105 | 9 | 2 | 5 |  | 34.5 |  |
| Finance > Service Payments > Unassigned TokenPayment | `/payg/paygtokenpayment/unassigned2` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Service Payments > No-Sale Payments | `/payg/paygtokenpayment/nosale2` | vue | 777 | 9 | 2 | 5 |  | 48.4 |  |
| Finance > Service Payments > Unassigned Payments | `/crud/payment/unassigned2` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Service Payments > Order Payments | `/crud/payment/orderpayments2` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Payroll > Defaulter snapshots | `/payroll/workerbehavioragent/defaulterssnapshots` | vue | 5971 | 10 | 2 | 2 |  | 45.9 |  |
| Finance > Payroll > Worker Monthly Commission | `/payroll/workerbehavioragent/workermonthlycommission` | vue |  | 18 | 2 | 6 |  | 36.0 |  |
| Finance > Payroll > Worker Transport Allowances | `/payroll/workerbehavioragent/workerweeklytransportallowances` | vue |  | 16 | 4 | 6 |  | 25.1 |  |
| Finance > Payroll > Agents Payroll | `/payroll/workerbehavioragent/index` | grid | 645 | 19 | 0 | 0 |  | 28.7 |  |
| Finance > Payroll > Transport Allowances | `/crud/worker/workertransportallowances` | grid | 699 | 14 | 13 | 0 |  | 41.6 |  |
| Finance > Payroll > Fully Paid Bonus | `/payg/paygdevice/sobonusreport` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Payroll > Worker deduction | `/payg/paygdevice/workerdeductions` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Budget > Create Budget | `/payroll/budgetexpenses/createbudget` | page |  | 0 | 0 | 0 |  | 36.2 |  |
| Finance > Budget > Budget Approximate | `/payroll/budgetexpenses/index2` | vue | 41 | 15 | 2 | 2 | /payroll/budgetexpenses/createbudget | 23.2 |  |
| Finance > Budget > Budget Approval | `/payroll/budgetexpenses/indexadmin2` | vue | 8626 | 12 | 2 | 4 |  | 4.2 |  |
| Finance > Budget > Budget Return | `/payroll/budgetexpenses/indexreturn2` | vue | 74 | 14 | 0 | 3 |  | 3.7 |  |
| Finance > Budget > Sales Point Budget | `/payroll/retailbudget/index` | vue | 0 | 17 | 0 | 2 | modal | 2.3 |  |
| Finance > Budget > Budget Summary | `/payroll/budgetexpenses/indexsummary2` | page |  | 0 | 0 | 0 |  | 18.0 |  |
| Finance > Budget > Non-Budget Expenses | `/payroll/budgetexpenses/indexnonbudget` | grid |  | 5 | 5 | 5 |  | 31.9 |  |
| Finance > Finance Reports > Outstanding Balance | `/report/default/outstandingbalance?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Finance Reports > Payments Per Provider | `/crud/payment/provider` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Finance Reports > Cash Collected | `/crud/sale/cashcollected?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Finance Reports > Profit & Loss Report | `/payroll/budgetexpenses/indexprofitloss` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Finance > Finance Reports > Annual Report | `/payroll/budgetexpenses/annualreport` | page |  | 0 | 0 | 0 |  | 44.8 |  |
| Finance > Solar reconciliation | `/payg/paygtokenpayment/solarreconciliation` | page |  | 0 | 0 | 0 |  | 45.7 |  |
| Survey > Payg Survey | `/survey/default/solar?start_exit=1` | page |  | 0 | 0 | 0 |  | 30.5 |  |
| Survey > Remainder Survey | `/survey/default/survey?start_exit=1&categories=17` | page |  | 0 | 0 | 0 |  | 61.0 |  |
| Survey > Worker Survey | `/survey/candidateworker/surveycandidate?start_exit=1` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Audit > All Audits | `/crud/auditreview/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Zones > District | `/crud/district/index?workerid=` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Zones > Ward | `/crud/ward/index?workerid=` | table |  | 5 | 0 | 0 | /crud/ward/create | 32.2 |  |
| Zones > Village | `/crud/village/index?workerid=` | table |  | 4 | 0 | 0 | /crud/village/create | 32.1 |  |
| Zones > Warehouse | `/crud/warehouse/index?workerid=` | table |  | 6 | 0 | 0 | /crud/warehouse/create | 45.2 |  |
| Tickets 0 > My Tickets | `/crud/ticket/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Tickets 0 > All Tickets | `/crud/ticket/indexall` | page |  | 0 | 0 | 0 |  | 61.2 |  |
| Sms > Inbox | `/sms/inbox/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sms > Outbox | `/sms/outbox/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sms > Sent SMS | `/sms/sentsms/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sms > Bulk SMS > SMS Workers | `/sms/outbox/smsworkers` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sms > Bulk SMS > SMS TLs | `/sms/outbox/smstls` | page |  | 0 | 0 | 0 |  | 60.0 |  |
| Sms > Bulk SMS > SMS Customer | `/sms/outbox/smscustomers` | page |  | 0 | 0 | 0 |  | 60.1 |  |
| Sms > Bulk SMS > Bulk Groups | `/sms/bulkgroup/index` | grid |  | 2 | 2 | 2 | /sms/bulkgroup/create | 60.1 |  |
| Sms > Bulk SMS > Import SMS | `/sms/outbox/upload` | page |  | 0 | 0 | 0 |  | 50.8 |  |
| Sms > Bulk SMS > GCM SMS | `/sms/default/gcm` | page |  | 0 | 0 | 0 |  | 54.1 |  |
| Sms > Contacts > All Contacts | `/sms/contact/index` | grid |  | 4 | 3 | 4 | /sms/contact/create | 52.5 |  |
| Sms > Contacts > Import Contacts | `/sms/contact/upload` | page |  | 0 | 0 | 0 |  | 57.4 |  |
| Sms > Settings > SMS Category | `/sms/smscategory/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sms > Settings > SMS Template | `/sms/template/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Sms > Settings > SMS Senders | `/sms/sms-sender/index` | vue | 0 | 4 | 2 | 4 | modal | 49.2 |  |
| Sms > Notification | `/sms/workernotification/index` | grid |  | 8 | 8 | 8 | /sms/workernotification/create | 40.1 |  |
| Sms > SMS Reports > SMS Summary | `/sms/default/index` | table |  | 2 | 0 | 0 |  | 40.5 |  |
| Sms > SMS Reports > SMS Operators | `/sms/default/operator` | table |  | 19 | 0 | 0 |  | 50.8 |  |
| Config > Manage Positions | `/menu/positions` | table |  | 8 | 0 | 0 |  | 48.7 |  |
| Config > Users | `/users/index2` | vue | 99 | 10 | 3 | 4 | /users/create2 | 38.8 |  |
| Config > Roles | `/role/index` | table |  | 5 | 0 | 0 | /role/create | 34.4 |  |
| Config > Permission | `/permission/index2` | vue | 1011 | 4 | 2 | 1 | /permission/create | 33.0 |  |
| Config > Manage Menus | `/menu/index` | vue |  | 11 | 0 | 0 | /menu/create | 21.7 |  |
| Config > Permission Group | `/permissiongroup/index2` | vue | 34 | 4 | 2 | 1 | /permissiongroup/create | 48.7 |  |
| Config > Value List | `/crud/valuelist/index2` | page |  | 0 | 0 | 0 |  | 50.4 |  |
| Config > survey > Survey Data | `/survey/surveydata/index` | grid | 3873975 | 6 | 5 | 6 | /survey/surveydata/create | 51.6 |  |
| Config > survey > Survey Question | `/survey/surveyquestion/index` | table |  | 10 | 0 | 0 | /survey/surveyquestion/create | 57.7 |  |
| Config > survey > Survey Category | `/survey/surveycategory/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Config > survey > Survey Valuelist | `/survey/surveyvaluelist/index` | page |  | 0 | 0 | 0 |  | 60.9 |  |
| Config > Administration > Notifications Config | `/crud/notificationconfig/index` | vue | 1 | 7 | 3 | 5 | /crud/notificationconfig/create | 45.5 |  |
| Config > Administration > Notification Type | `/crud/notificationtype/index` | vue | 27 | 3 | 3 | 2 | /crud/notificationtype/create | 27.9 |  |
| Config > Administration > Farmer group Order status | `/crud/farmergrouporderstatus/index` | vue | 5 | 3 | 3 | 2 | /crud/farmergrouporderstatus/create | 14.0 |  |
| Config > Administration > Purchase category | `/crud/purchaserequestcategory/index` | vue | 6 | 4 | 3 | 2 | /crud/purchaserequestcategory/create | 2.0 |  |
| Config > Administration > Department | `/crud/department/index` | vue | 15 | 6 | 3 | 2 | /crud/department/create | 5.3 |  |
| Config > Administration > Organization Position | `/crud/organizationpositions/index` | vue | 48 | 7 | 3 | 3 | /crud/organizationpositions/create | 5.4 |  |
| Config > Administration > Vendors > All Vendor | `/crud/vendors/index` | vue | 0 | 6 | 3 | 2 | /crud/vendors/create | 4.6 |  |
| Config > Administration > Vendors > Vendor request Category | `/crud/vendorsrequestcategory/index` | vue | 0 | 5 | 3 | 2 | /crud/vendorsrequestcategory/create | 5.0 |  |
| Apps > Device Info | `/crud/deviceinfo/index` | table |  | 8 | 0 | 0 | /crud/deviceinfo/create | 14.5 |  |
| Apps > API Hit Log | `/crud/apihitlog/index` | grid |  | 6 | 5 | 5 | /crud/apihitlog/create | 29.4 |  |
| Apps > Sync Log | `/crud/synclog/index` | table |  | 6 | 0 | 0 | /crud/synclog/create | 91.1 |  |
| Apps > Complete Sync | `/crud/completesync/index` | table |  | 6 | 0 | 0 | /crud/completesync/create | 102.6 |  |
| Customer Service > Service Page | `/customerservice/index` | page |  | 0 | 0 | 0 |  | 34.9 |  |
| Customer Service > Shops Info | `/customerservice/shopsinfo` | vue | 7223 | 7 | 0 | 4 |  | 24.7 |  |
| Reports | `/reports` | page |  | 0 | 0 | 0 |  | 12.3 |  |
| Assets > All Assets | `/crud/asset/index` | vue | 24 | 11 | 3 | 8 | /crud/asset/create | 23.4 |  |
| Assets > Asset Names | `/crud/assetnames/index` | vue | 14 | 3 | 3 | 2 | /crud/assetnames/create | 12.4 |  |
| Purchase Request | `/crud/purchaserequest/index` | vue | 0 | 9 | 3 | 5 | /crud/purchaserequest/create | 12.0 |  |
