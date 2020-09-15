# packages to be imported 
from flask import Flask, jsonify, request 
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import MonthEnd
import calendar
import pandas as pd
import numpy as np
import pyodbc 

# Define the interest rate split; Take the annual interest rate and divide by 12
def IR(IntR):
    Intrate = float(IntR)/12
    return Intrate

# event to process/transform the input URL attributes; Will build on it eventually to add other attributes
def event(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term):
    dateList=[]
    LoanAmtList = []
    if(D_date1!="0"):
        # convert last day of month disb into one day prior for processing; Does not affect the table structure; 
        date1 = pd.to_datetime(D_date1, format = "%Y-%m-%d" )
        last_day_of_month = calendar.monthrange(date1.year, date1.month)[1]
        if(date1==date(date1.year, date1.month, last_day_of_month)):
            # change it to previous date
            date_step = datetime.strftime(date1 - timedelta(1), '%Y-%m-%d')
            dateList.append(str(date_step))
        else:
            dateList.append(D_date1)    
    if(D_date2!="0"):
        # convert last day of month disb into one day prior for processing; Does not affect the table structure; 
        date2 = pd.to_datetime(D_date2, format = "%Y-%m-%d" )
        last_day_of_month = calendar.monthrange(date2.year, date2.month)[1]
        if(date2==date(date2.year, date2.month, last_day_of_month)):
            # change it to previous date
            date_step = datetime.strftime(date2 - timedelta(1), '%Y-%m-%d')
            dateList.append(str(date_step))
        else:
            dateList.append(D_date2)
    if(D_date3!="0"):
        # convert last day of month disb into one day prior for processing; Does not affect the table structure; 
        date3 = pd.to_datetime(D_date3, format = "%Y-%m-%d" )
        last_day_of_month = calendar.monthrange(date3.year, date3.month)[1]
        if(date3==date(date3.year, date3.month, last_day_of_month)):
            # change it to previous date
            date_step = datetime.strftime(date3 - timedelta(1), '%Y-%m-%d')
            dateList.append(str(date_step))
        else:
            dateList.append(D_date3)
    if(D_date4!="0"):
        # convert last day of month disb into one day prior for processing; Does not affect the table structure; 
        date4 = pd.to_datetime(D_date4, format = "%Y-%m-%d" )
        last_day_of_month = calendar.monthrange(date4.year, date4.month)[1]
        if(date4==date(date4.year, date4.month, last_day_of_month)):
            # change it to previous date
            date_step = datetime.strftime(date4 - timedelta(1), '%Y-%m-%d')
            dateList.append(str(date_step))
        else:
            dateList.append(D_date4)
    if(Loan_Amount1!=0):
        LoanAmtList.append(Loan_Amount1)
    if(Loan_Amount2!=0):
        LoanAmtList.append(Loan_Amount2)
    if(Loan_Amount3!=0):
        LoanAmtList.append(Loan_Amount3)
    if(Loan_Amount4!=0):
        LoanAmtList.append(Loan_Amount4)
    # logic to handle same month, same day disbursement
    dates = [datetime.strptime(d, "%Y-%m-%d") for d in dateList]
    counter = 0
    amt=0
    while(counter!=len(dates)-1):
        if(dates[counter].year == dates[counter+1].year and dates[counter].month == dates[counter+1].month):
            amt = LoanAmtList[counter]+LoanAmtList[counter+1]
            LoanAmtList[counter+1]=amt
            LoanAmtList[counter] = 0
            dateList[counter] = 0
        counter = counter+1
    dateList = [i for i in dateList if i != 0]
    LoanAmtList = [x for x in LoanAmtList if x != 0]
    return dateList, Repayment_Option, Expected_Graduation_Date, Repayment_Term, LoanAmtList

# To calculate the deferment term separtely
def deferment_calc(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term):
    Disb_date, Repayment_Option, Expected_Graduation_Date, Repayment_Term, Loan_Amount = event(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term)
    if(Repayment_Option == 'IM'): # only for IM loans
        last_disb = Disb_date[-1] # An applicant does not have a deferment term; we take the last/final disbursement
        repay_begin_dt = datetime.strptime(last_disb, "%Y-%m-%d")
        # + relativedelta(months=+2) # Applicant also has about 60 days to begin repayment; thereby adding a couple of months
        d = str(datetime.date(repay_begin_dt))
        def_term = ((datetime.strptime(d, "%Y-%m-%d").year) - (datetime.strptime(last_disb, "%Y-%m-%d").year)) * 12 + (datetime.strptime(d, "%Y-%m-%d").month - datetime.strptime(last_disb, "%Y-%m-%d").month)    
        def_term = def_term+1
    else:
        last_disb = Disb_date[-1] # taking the final disbursement date
        repay_begin_dt = datetime.strptime(last_disb, "%Y-%m-%d") + relativedelta(months=+1) # setting the repayment begin date to next month from final disbursement; Interest accrues from this date
        def_term = ((datetime.strptime(Expected_Graduation_Date, "%Y-%m-%d").year) - (datetime.strptime(last_disb, "%Y-%m-%d").year)) * 12 + (datetime.strptime(Expected_Graduation_Date, "%Y-%m-%d").month - datetime.strptime(last_disb, "%Y-%m-%d").month)
        if(def_term<=65): #Condition to keep the total deferment term to less than or equal to 66 months 
            def_term = def_term+1
        else:
            def_term = 66   
    return datetime.date(repay_begin_dt), def_term
    

# function to create the timeline of the loan based on 3 statuses 
def tble(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term):
    Disb_date, Repayment_Option, Expected_Graduation_Date, Repayment_Term, Loan_Amount = event(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term)
    first_disb = datetime.strptime(Disb_date[0],"%Y-%m-%d")  
    last_disb = datetime.strptime(Disb_date[-1],"%Y-%m-%d")
    status = []
    period_inStatus = []
    final_dates = [] # this list will have the final list of dates in the amoritization schedule
    repay_begin_dt, defer_term = deferment_calc(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term)
    defer_dates = pd.date_range(first_disb,last_disb + relativedelta(months=+defer_term), freq='M').tolist() # generates dates only for deferment period
    if(Repayment_Option!="IM"):
        Final_Repay_term = Repayment_Term 
        grace_dates = pd.date_range(max(defer_dates) + relativedelta(months=+1),max(defer_dates) + relativedelta(months=+7), freq='M').tolist() # generates dates only for grace period
        repay_dates = pd.date_range(max(grace_dates) + relativedelta(months=+1), max(grace_dates) + relativedelta(months=+Final_Repay_term), freq='M').tolist() # generates dates only for repayment period   
        all_dates = (defer_dates+grace_dates+repay_dates)
    else:
        if(len(Disb_date)>3):
            Final_Repay_term = Repayment_Term-len(defer_dates)+1 # number of disbursements when 4 ; requires the +1 factor; else not required 
        else:
            Final_Repay_term = Repayment_Term-len(defer_dates)
        repay_dates = pd.date_range(max(defer_dates)+relativedelta(months=+1), max(defer_dates) + relativedelta(months=+Final_Repay_term), freq='M').tolist() # generates dates only for repayment period
        all_dates = (defer_dates+repay_dates)
     # combining all the above lists in order of execution
    for dates in all_dates:
        final_dates.append(dates.strftime("%Y-%m-%d"))
        period_index = all_dates.index(dates)
        period_index += 1
        period_inStatus.append(period_index) # this gives us the timeperiod of the repayment life cycle
    if(Repayment_Option!="IM"):
        for dates in all_dates:
            if(dates >= first_disb and dates <= last_disb+relativedelta(months=+defer_term)): # condition for deferment 
                status_now = 'In-School'
                status.append(status_now)
            elif(dates >= max(defer_dates)+relativedelta(months=+1) and dates <= max(defer_dates)+relativedelta(months=+7)): # condition for grace
                status_now = 'Grace'
                status.append(status_now)
            else: # condition for repayment 
                status_now = 'Repayment'
                status.append(status_now)
    else:
        for dates in all_dates:
            if(dates >= first_disb and dates <= last_disb+relativedelta(months=+defer_term)): # condition for deferment 
                status_now = 'In-School'
                status.append(status_now)
            else: # condition for repayment 
                status_now = 'Repayment'
                status.append(status_now)
    return final_dates, period_inStatus, status

# function to add the loan amount based on the disbursement date to the schedule table 
def disburs(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term):
    disbAmtList = []
    Increase_Loan_Amount = 0
    Disb_date, Repayment_Option, Expected_Graduation_Date, Repayment_Term, Loan_Amount = event(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term)
    final_dates, period_inStatus, status = tble(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term)
    for dates in final_dates:
        for a in range(len(Disb_date)):
            if(Disb_date[a]!= dates):
                last_date = datetime.strftime(pd.to_datetime(Disb_date[a], format = "%Y-%m-%d" )+MonthEnd(1), "%Y-%m-%d") 
            else:
                last_date = datetime.strftime(pd.to_datetime(Disb_date[a], format = "%Y-%m-%d" ), "%Y-%m-%d") 
            if (dates == last_date): # only adding the loan amounts to this list 
                Increase_Loan_Amount = Loan_Amount[a] # this is causing the problem - somehow automate this
                break
            else:
                Increase_Loan_Amount = '-'
        disbAmtList.append(Increase_Loan_Amount)    
    return final_dates, period_inStatus, status, disbAmtList

# create the product offering; so as to pull only the data that matters from SQL server
def productOffering(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList = disburs(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term)
    PO_List = []
    for a in range(len(period_inStatus)):
        product_offer = PO
        PO_List.append(product_offer)
    return final_dates, period_inStatus, status, disbAmtList, PO_List

# create database connection and get the curve values stored in the dataframe
def curve_database(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList, PO_List = productOffering(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    unit_defaults=[]
    unit_severity=[]
    unit_ParPrepay=[]
    unit_FullPrepay=[]
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                        "Server=QW16BTSQL08;"
                        "Database=SLAM;"
                        "uid=pkhari;pwd=prasnnaCMDW16;"
                        "Trusted_Connection=no;")
    SQL_Query = pd.read_sql_query("select typecd, Performance_Paramenter_Period, Performance_Paramenter_Value from dbo.v_Curve_Variables where Product_Offering ="+"'"+PO+"'"+";", cnxn)
    df = pd.DataFrame(SQL_Query, columns=['typecd', 'Performance_Paramenter_Period','Performance_Paramenter_Value']) # stored the corresponding default curve values into a dataframe
    # Replacing the blank values with NUll; handling Index out of bounds exception
    try:
        endpoint_default = df[(df['typecd']=="EDFT")]['Performance_Paramenter_Value'].values[0]
    except IndexError:
        endpoint_default = 0
    try:
        endpoint_ParPrepay = df[(df['typecd']=="EPPPY")]['Performance_Paramenter_Value'].values[0]
    except IndexError:
        endpoint_ParPrepay = 0
    try:
        endpoint_FullPrepay = df[(df['typecd']=="EFPPY")]['Performance_Paramenter_Value'].values[0]
    except IndexError:
        endpoint_FullPrepay = 0
    for a in range(len(period_inStatus)):
        try:
            unit_def_curve_val = df[(df['Performance_Paramenter_Period']==a) & (df['typecd']=="UDFT")]['Performance_Paramenter_Value'].values[0]
        except IndexError:
            unit_def_curve_val = 0
        unit_defaults.append(unit_def_curve_val)
        try:
            sev_curve_val = df[(df['Performance_Paramenter_Period']==a+1) & (df['typecd']=="SEV")]['Performance_Paramenter_Value'].values[0]
        except IndexError:
            sev_curve_val = 0
        unit_severity.append(sev_curve_val)
        try:
            pp_curve_val = (df[(df['Performance_Paramenter_Period']==a+1) & (df['typecd']=="PPPY")]['Performance_Paramenter_Value'].values[0])/100
        except IndexError:
            pp_curve_val = 0
        unit_ParPrepay.append(pp_curve_val)
        try:
            fpp_curve_val = df[(df['Performance_Paramenter_Period']==a+1) & (df['typecd']=="FPPY")]['Performance_Paramenter_Value'].values[0]
        except IndexError:
            fpp_curve_val = 0
        unit_FullPrepay.append(fpp_curve_val)
    return endpoint_default, endpoint_ParPrepay, endpoint_FullPrepay, unit_defaults, unit_severity, unit_ParPrepay, unit_FullPrepay
    #print(endpoint_default, endpoint_ParPrepay, endpoint_FullPrepay, unit_defaults, unit_severity, unit_ParPrepay, unit_FullPrepay)

# incorporating the curve data before capitalization
def curve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList, PO_List = productOffering(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    endpoint_default, endpoint_ParPrepay, endpoint_FullPrepay, unit_defaults, unit_severity, unit_ParPrepay, unit_FullPrepay = curve_database(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    Anticipated_Def_Amt = []
    amt=0
    Anticipated_PartialPrepay_Amt = []
    Anticipated_FullPrepay_Amt=[]
    for a in range(len(period_inStatus)):
        if(disbAmtList[a]!="-"):
            amt+=disbAmtList[a] 

            monthly_unit_defrate = endpoint_default*unit_defaults[a]
            monthly_def_amt = round(unit_severity[a]*monthly_unit_defrate*amt,2)
            Anticipated_Def_Amt.append(monthly_def_amt)


            monthly_unit_PPRate = endpoint_ParPrepay*unit_ParPrepay[a]
            monthly_PP_amt = round(amt * monthly_unit_PPRate,2)
            Anticipated_PartialPrepay_Amt.append(monthly_PP_amt)

            monthly_unit_PrepayRate = endpoint_FullPrepay*unit_FullPrepay[a]
            monthly_Prepay_amt = round(amt*monthly_unit_PrepayRate,2)
            Anticipated_FullPrepay_Amt.append(monthly_Prepay_amt)

        else:
            monthly_unit_defrate = endpoint_default*unit_defaults[a]
            monthly_def_amt = round(unit_severity[a]*monthly_unit_defrate*amt,2)
            Anticipated_Def_Amt.append(monthly_def_amt)

            monthly_unit_PPRate = endpoint_ParPrepay*unit_ParPrepay[a]
            monthly_PP_amt = round(amt * monthly_unit_PPRate,2)          
            Anticipated_PartialPrepay_Amt.append(monthly_PP_amt)

            monthly_unit_PrepayRate = endpoint_FullPrepay * unit_FullPrepay[a]
            monthly_Prepay_amt = round(amt*monthly_unit_PrepayRate,2)
            Anticipated_FullPrepay_Amt.append(monthly_Prepay_amt)
    return final_dates, period_inStatus, status, disbAmtList, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt


# Define a function to get the Interest accrural list and capitalisation phase before repayment begins
def intStruc_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt = curve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    ls = [a for a, e in enumerate(disbAmtList) if e!="-"]
    indices = [i for i, x in enumerate(status) if x == "In-School"]
    last_index = max(indices)
    amts = 0
    cum_disb_aftercurve=[]
    for i in range(len(final_dates)):
        if(status[i] == "In-School" or status[i]=="Grace"):
            if(i in ls): # if else block to get the cummulative disbursement amounts; so that we can calculate the interest accrued over at every step
                amts+=disbAmtList[i]
                amts = amts - (Anticipated_Def_Amt[i] + Anticipated_FullPrepay_Amt[i] + Anticipated_PartialPrepay_Amt[i])
                cum_disb_aftercurve.append(amts)
            else:
                amts = amts - (Anticipated_Def_Amt[i] + Anticipated_FullPrepay_Amt[i] + Anticipated_PartialPrepay_Amt[i])
                cum_disb_aftercurve.append(amts)
        else:
            cum_disb_aftercurve.append(0)
    return final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt


# get the interest accrual piece at every month until repayment begins
def interest_calc_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt = intStruc_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    interest_aftercurve=[]
    amts = [float(i) for i in cum_disb_aftercurve]
    rate = IR(IntR)
    for i in range(len(amts)):
        if(amts[i] != 0):
            calc = amts[i]*(rate/100)
            interest_aftercurve.append(str(calc))
        else:
            interest_aftercurve.append("0")
    return final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt

# minimum payment during deferments ; Similar for IO, PI, DF; IM - there wont be a minimum payment associated because they get into repayment right after disbursement
def Minimum_Payment_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt = interest_calc_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    min_Pay_aftercurve=[]
    for c in range(len(interest_aftercurve)):
        if(status[c] == "In-School" or status[c] == "Grace"):
            if(Repayment_Option == "IO"):
                min_Pay_aftercurve.append(interest_aftercurve[c])
            elif(Repayment_Option == "PI"):
                min_Pay_aftercurve.append(float(25))
            else:
                min_Pay_aftercurve.append(float(0))
        else:
            min_Pay_aftercurve.append(float(0))
    return final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, min_Pay_aftercurve,PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt



# calculate the capitalization piece/flag and get the total amount due after deferment period and grace
def capitalisation_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, min_Pay_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt = Minimum_Payment_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    capitalisationList_aftercurve=[]
    if(Repayment_Option!="IM"):
        indices = [i for i, x in enumerate(status) if x == "Grace"]
        last_index = max(indices)
    else:
        indices = [i for i, x in enumerate(status) if x == "In-School"]
        last_index = max(indices)
    for i in range(len(final_dates)):
        if(i == last_index):
            Int_amts_tot = [float(i) for i in interest_aftercurve]
            min_PayAmts_tot = [float(j) for j in min_Pay_aftercurve]
            amount = sum(Int_amts_tot)+cum_disb_aftercurve[last_index]-sum(min_PayAmts_tot)
            capitalisationList_aftercurve.append(amount)
        else:
            capitalisationList_aftercurve.append(0)
    return final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, min_Pay_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt, capitalisationList_aftercurve


# to get the rest of the anticipated full prepayment curves
def complete_Anticip_FPPYList(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, min_Pay_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt, capitalisationList_aftercurve = capitalisation_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    endpoint_default, endpoint_ParPrepay, endpoint_FullPrepay, unit_defaults, unit_severity, unit_ParPrepay, unit_FullPrepay = curve_database(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    
    InterestRate = np.round(IR(IntR)/100,3) # interest rate required

    if(Repayment_Option!="IM"):
        indices = [i for i, x in enumerate(status) if x == "Grace"]
        last_index = max(indices)
    else:
        indices = [i for i, x in enumerate(status) if x == "In-School"]
        last_index = max(indices)

    repay_Start_Index = last_index + 1

    del Anticipated_FullPrepay_Amt[repay_Start_Index:]

    if(Repayment_Option!="IM"):
        RepaymentTerm_Mos = Repayment_Term+1# repayment term required in months
    else:
        RepaymentTerm_Mos = Repayment_Term-repay_Start_Index


    principal_paid=[]
    interest_paid=[]
    total_payment=[]
    ending_balance=[]

    # for first ending balance
    cap_amt_first_eBal = round(capitalisationList_aftercurve[last_index],2)

    for per in range(RepaymentTerm_Mos):
        principal_Paid = -np.ppmt(InterestRate, per, RepaymentTerm_Mos, cap_amt_first_eBal)
        principal_paid.append(principal_Paid)
        interest_Paid = -np.ipmt(InterestRate, per, RepaymentTerm_Mos, cap_amt_first_eBal)
        interest_paid.append(interest_Paid)
        total_payment.append(principal_Paid+interest_Paid)

    # calculating the ending balance at each period
    for i in range(repay_Start_Index, len(status)):
        if(status[i]=="In-School" or status[i]=="Grace"):
            ending_balance.append("-")
            interest_paid.append("-")
            total_payment.append("-")
            principal_paid.append("-")
        else:
            i = i-repay_Start_Index
            start_previous_bal =  cap_amt_first_eBal-principal_paid[i]
            ending_balance.append(start_previous_bal)
            first_fullPrepay_calc = start_previous_bal*endpoint_FullPrepay*unit_FullPrepay[repay_Start_Index] # prior month ending principal * current month Full prepay unit
            Anticipated_FullPrepay_Amt.append(first_fullPrepay_calc)
            cap_amt_first_eBal = start_previous_bal
    return final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, min_Pay_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt, capitalisationList_aftercurve 

# create the repayment schedule:
def paydown_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, min_Pay_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt, capitalisationList_aftercurve = complete_Anticip_FPPYList(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    endpoint_default, endpoint_ParPrepay, endpoint_FullPrepay, unit_defaults, unit_severity, unit_ParPrepay, unit_FullPrepay = curve_database(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)
    Curr_Balance=[]
    Interest_repay=[]
    Payment=[]
    Principal=[]

    InterestRate = np.round(IR(IntR)/100,3) # interest rate required

    if(Repayment_Option!="IM"):
        indices = [i for i, x in enumerate(status) if x == "Grace"]
        last_index = max(indices)
        repay_Start_Index = last_index + 1
        RepaymentTerm_Mos = Repayment_Term
    else:
        indices = [i for i, x in enumerate(status) if x == "In-School"]
        last_index = max(indices)
        repay_Start_Index = last_index + 2
        RepaymentTerm_Mos = Repayment_Term-repay_Start_Index


    repayment_begin_date = final_dates[repay_Start_Index] # to get the repayment start date

    repayment_end_date = final_dates[-1] # to get the repayment end date

    # specifying the structure of the repayment schedule
    rng = pd.date_range(repayment_begin_date, periods=RepaymentTerm_Mos, freq='MS')
    rng.name = "Payment Date"
    df = pd.DataFrame(index=rng, columns=['Payment', 'Principal Paid', 'Interest Paid', 'Ending Balance'], dtype='float')
    df.reset_index(inplace=True)
    df.index += 1
    df.index.name = "Period"

    # for first ending balance
    capitalisation_amt = round(capitalisationList_aftercurve[last_index],2)
    df.loc[1, "Principal Paid"] = -1* np.ppmt(InterestRate, 1, RepaymentTerm_Mos, capitalisation_amt)
    df.loc[1, "Interest Paid"] = -1* np.ipmt(InterestRate, 1, RepaymentTerm_Mos, capitalisation_amt)
    df.loc[1, "Payment"] = df.loc[1, "Principal Paid"] + df.loc[1, "Interest Paid"]

    # calculating the first ending balance
    #df["Ending Balance"]=0
    Anticipated_Amts= Anticipated_Def_Amt[last_index]+ Anticipated_FullPrepay_Amt[last_index]+ Anticipated_PartialPrepay_Amt[last_index]
    df.loc[1, "Ending Balance"] = capitalisation_amt-df.loc[1, "Principal Paid"]-Anticipated_Amts

    # rounding up
    df = df.round(2)

    # looping through to get the final ending balance to be zero
    for period in range(2, len(df)):
        previous_bal = df.loc[period-1, 'Ending Balance'] - Anticipated_Def_Amt[last_index+(period-1)] - Anticipated_FullPrepay_Amt[last_index+(period-1)] - Anticipated_PartialPrepay_Amt[last_index+(period-1)] 
        principal_paid = df.loc[period, "Principal Paid"]
        if previous_bal == 0 or previous_bal == "nan":
            df.loc[period, ['Payment', 'Principal Paid', 'Interest Paid', 'Ending Balance']] == 0
            continue
        elif principal_paid <= previous_bal:
            df.loc[period, 'Ending Balance'] = previous_bal - principal_paid  
    # rounding up        
    df = df.round(2)
    for _ in range(0, last_index+1):
        Curr_Balance.append("-")
        Interest_repay.append("-")
        Payment.append("-")
        Principal.append("-")
    # convert dataframe to lists and then append them to the above lists 
    inter_step_CB = df['Ending Balance'].to_list() 
    Curr_Balance.extend(inter_step_CB)
    inter_step_int = df['Interest Paid'].to_list() 
    Interest_repay.extend(inter_step_int)
    inter_step_pay = df['Payment'].to_list() 
    Payment.extend(inter_step_pay)
    inter_step_prin = df['Principal Paid'].to_list() 
    Principal.extend(inter_step_prin)
    df_table = pd.DataFrame(np.column_stack([final_dates, period_inStatus, status, disbAmtList, cum_disb_aftercurve, interest_aftercurve, min_Pay_aftercurve, PO_List, Anticipated_Def_Amt, Anticipated_PartialPrepay_Amt, Anticipated_FullPrepay_Amt, capitalisationList_aftercurve, Principal, Interest_repay, Payment, Curr_Balance]), columns=['Date','Period_inStatus', 'Status', 'Disbursement_Amount_inPeriod', 'Cummulative_Disbursement_Amount', 'Deferment_Grace_interest_Amount', 'Deferment_Grace_Min_Payment','Product_OfferingCode', 'Anticipated_Default_Amount', 'Anticipated_PartialPrepay_Amount', 'Anticipated_FullPrepay_Amount', 'capitalisation', 'Repayment_Principal_Payment', 'Repayment_Interest_Payment', 'Repayment_Total_Payment', 'Repayment_Principal_Paydown']) 
    df_table = df_table.round(3)
    output = df_table.to_dict('records')
    return jsonify(output)

# Initializing the web app
app = Flask(__name__) 
# route to be used in the SQL HTTP request
@app.route('/<string:D_date1>/<float:Loan_Amount1>/<string:D_date2>/<float:Loan_Amount2>/<string:D_date3>/<float:Loan_Amount3>/<string:D_date4>/<float:Loan_Amount4>/<string:Repayment_Option>/<string:Expected_Graduation_Date>/<int:Repayment_Term>/<float:IntR>/<string:PO>', methods = ['GET']) 

def run(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO):
    return paydown_aftercurve(D_date1, Loan_Amount1, D_date2, Loan_Amount2, D_date3, Loan_Amount3, D_date4, Loan_Amount4, Repayment_Option, Expected_Graduation_Date, Repayment_Term, IntR, PO)

# driver function 
import warnings
if __name__ == '__main__':   
    warnings.filterwarnings("ignore")
    app.run(host= "10.200.50.68", debug = True) 