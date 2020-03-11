from flask import *
from functools import wraps
import smtplib
import random
import string
from flask_mysqldb import MySQL
import datetime
from datetime import timedelta
app = Flask(__name__)


app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '#Boeing747'
app.config['MYSQL_DB'] = 'crg_g3_quarterly'

curr_month = datetime.datetime.now()
current_month = curr_month.strftime("%B")

if current_month in ['July','August','September']:
    quarter = 2
elif current_month in ['October','November','December']:
    quarter = 3
elif current_month in ['January','February','March']:
    quarter = 4
else:
    quarter = 1

mysql = MySQL(app)
app.secret_key = 'secret key6' #Use a random key generator

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)

def otp_genrator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

@app.route("/",methods=['GET','POST'])
@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        userDetails = request.form
        email_id = userDetails['email']
        cur = mysql.connection.cursor()
        sql = 'select Emp_Email from emp_master_zoho where Emp_Email="'+str(email_id)+'"'
        cur.execute(sql)
        data = cur.fetchall()[0][0]
        mysql.connection.commit()
        cur.close()
        if data is None:
            return render_template('woops.html')
        else:
            return redirect('/otp/'+str(email_id))
    return render_template("login.html")

@app.route("/otp/<email>",methods=['GET','POST'])
def otp(email):
    if request.method == 'POST':
        otpNumber = request.form
        otpNumber = otpNumber['otp_num']
        em = email
        # Checking otp
        cur = mysql.connection.cursor()
        sql_qry = "select email,otp_value from otp where email='"+str(em)+"'"
        cur.execute(sql_qry)
        mysql.connection.commit()
        otp_data = cur.fetchall()
        cur.close()
        if otp_data[0][1] == otpNumber:
            cur = mysql.connection.cursor()
            # Getting details of the logged in Employee
            sql_qry = "select * from emp_master_zoho where Emp_Email='"+str(em)+"'"
            cur.execute(sql_qry)
            mysql.connection.commit()
            emp_data = cur.fetchall()
            emp_band = emp_data[0][5]
            emp_id = emp_data[0][1]
            cur.close()

            session['logged_in'] = True
            session['email'] = em
            session['logged_emp_id'] = emp_id
            return redirect("/rm_welcome")
        else:
            return render_template("woops.html")
    em = email
    val = otp_genrator()
    cur = mysql.connection.cursor()
    sql_qry = "insert into otp (email,otp_value) values(%s,%s)"
    cur.execute(sql_qry, [str(em), str(val)])
    mysql.connection.commit()
    cur.close()
    # Preparing To send Mail for OTP
    TO = em
    SUBJECT = 'OTP for quarterly login'
    TEXT = 'Your OTP is: '+str(val)+', It is valid only for 1 minute!'

    # Gmail Sign In
    gmail_sender = 'kkalambe@crgroup.co.in'
    gmail_passwd = '#Boeing747'

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(gmail_sender, gmail_passwd)

    BODY = '\r\n'.join(['To: %s' % TO,
                        'From: %s' % gmail_sender,
                        'Subject: %s' % SUBJECT,
                        '', TEXT])
    try:
        # server.sendmail(gmail_sender, [TO], BODY)
        print('email sent')
    except:
        print('error sending mail')
    server.quit()
    return render_template("enter_otp.html", data=em)

@app.route("/success",methods=['GET','POST'])
def success():
    return render_template("success.html")

@app.route("/g3_self_form",methods=['GET','POST'])
@login_required
def g3_self_form():
    if request.method == 'POST':
        self_review = request.form
        emp_id = self_review['emp_id']
        on_time_task_comp = self_review['Q1']
        project_mgmt_prtl_updt = self_review['Q2']
        customer_exp_quality = self_review['Q3']
        attendance_zoho = self_review['Q4']
        reporting_expense = self_review['Q5']
        project_or_daily_status = self_review['Q6']
        project_documentation = self_review['Q7']
        tableau_alteryx_dw = self_review['Q8']
        zoho_connect = self_review['Q9']
        attend_trainings = self_review['Q10']
        appreciation = self_review['Q11']
        opportunity = self_review['Q12']
        cur = mysql.connection.cursor()
        sql_qry = "insert into g3_self_rating values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(sql_qry, [emp_id, quarter, int(on_time_task_comp), int(project_mgmt_prtl_updt),
                              int(customer_exp_quality), int(attendance_zoho), int(reporting_expense),
                              int(project_or_daily_status), int(project_documentation), int(tableau_alteryx_dw),
                              int(zoho_connect), int(attend_trainings), appreciation, opportunity])
        mysql.connection.commit()
        cur.close()
        return redirect('/success')
    return render_template("g3_self_form.html", results=session['logged_emp_id'])

# Via a AJAX request the below form must be able to fetch self input data of a G3
# The fetched data must come based on the inputs passed by the user
# Data for the respective reporting manager must only come for the given RM

@app.route("/rm_welcome",methods=['GET','POST'])
@login_required
def rm_welcome():
    # Collecting logged in user's reportees if he/she is Reporting Manager
    reportees = []
    cur = mysql.connection.cursor()
    logged_rm = session['logged_emp_id']
    sql_qry = "select emp_id from emp_master_zoho where RM_ID='"+str(logged_rm)+"';"
    cur.execute(sql_qry)
    emp_id_data = cur.fetchall()
    for x in emp_id_data:
        reportees.append(x[0])
    mysql.connection.commit()
    cur.close()
    # Collecting logged in users reportees completed

    # Collecting logged in user's reportees if he/she is Project Lead
    reportees_pl = []
    cur = mysql.connection.cursor()
    logged_rm = session['logged_emp_id']
    sql_qry = "select emp_id from emp_master_zoho where PL_ID='" + str(logged_rm) + "';"
    cur.execute(sql_qry)
    emp_id_data_pl = cur.fetchall()
    for x in emp_id_data_pl:
        reportees_pl.append(x[0])
    mysql.connection.commit()
    cur.close()
    # Collecting logged in users reportees completed

    def get_all_emp():
        # Collecting logged all users
        all_reportees = []
        cur = mysql.connection.cursor()
        logged_rm = session['logged_emp_id']
        sql_qry = "select emp_id from emp_master_zoho;"
        cur.execute(sql_qry)
        emp_id_data_pl = cur.fetchall()
        for x in emp_id_data_pl:
            all_reportees.append(x[0])
        mysql.connection.commit()
        cur.close()
        return all_reportees
        # Collecting all users completed
    if session['email'] == 'hr@crgroup.co.in':
        all_reportees_hr = get_all_emp()
        all_reportees = []
    elif session['email'] == 'hsethi@crgroup.co':
        all_reportees = get_all_emp()
        all_reportees_hr = []
    else:
        all_reportees = []
        all_reportees_hr = []

    if request.method == 'POST':
        emp_details = request.form
        try:
            emp_id = emp_details['reportee_id']
            return redirect('/g3_rm_form/'+str(emp_id))
        except:
            try:
                emp_id = emp_details['reportee_id_pl']
                return redirect('/g3_pl_form/' + str(emp_id))
            except:
                if session['email'] == 'hr@crgroup.co.in':
                    emp_id = emp_details['reportee_all_hr']
                    return redirect('/g3_hr_form/' + str(emp_id))
                elif session['email'] == 'hsethi@crgroup.co':
                    emp_id = emp_details['reportee_all']
                    return redirect('/g3_bh_form/' + str(emp_id))
    return render_template("rm_welcome.html", results=([reportees, reportees_pl, all_reportees_hr, all_reportees]))

@app.route("/g3_rm_form/<reportee_id>", methods=['GET','POST'])
@login_required
def g3_rm_form(reportee_id):
    reportee = [reportee_id]
    cur = mysql.connection.cursor()
    # Check if this RM owns this Reportee
    check_sql = "select * from emp_master_zoho where Emp_ID='"+str(reportee[0])+"' and RM_ID='"+str(session['logged_emp_id'])+"'"
    check_validity = cur.execute(check_sql)
    if check_validity == 0:
        return 'Will you just mind your own business?'
    sql_qry = "select * from g3_self_rating where emp_id='" + str(reportee[0]) + "'"
    cur.execute(sql_qry)
    emp_ratings = cur.fetchall()
    if len(emp_ratings) == 0:
        emp_ratings = [0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0,
                       0, 0, 0, 0]
    else:
        emp_ratings = list(emp_ratings[0])

    if request.method == 'POST':
        self_review = request.form
        reportee_iden = self_review['reportee_iden']
        on_time_task_comp = self_review['Q1_RM']
        project_mgmt_prtl_updt = self_review['Q2_RM']
        customer_exp_quality = self_review['Q3_RM']
        attendance_zoho = self_review['Q4_RM']
        reporting_expense = self_review['Q5_RM']
        project_or_daily_status = self_review['Q6_RM']
        project_documentation = self_review['Q7_RM']
        tableau_alteryx_dw = self_review['Q8_RM']
        zoho_connect = self_review['Q9_RM']
        attend_trainings = self_review['Q10_RM']
        appreciation = self_review['Q11_RM']
        opportunity = self_review['Q12_RM']
        cur = mysql.connection.cursor()
        sql_qry = "insert into rm_g3_rating values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(sql_qry, [reportee_iden, quarter, int(on_time_task_comp),int(project_mgmt_prtl_updt), int(customer_exp_quality), int(attendance_zoho),
                             int(reporting_expense), int(project_or_daily_status), int(project_documentation), int(tableau_alteryx_dw),
                             int(zoho_connect), int(attend_trainings), appreciation, opportunity])
        mysql.connection.commit()
        cur.close()
        return redirect('/success')
    return render_template("g3_rm_form.html", results=(reportee, emp_ratings))

@app.route("/g3_pl_form/<reportee_id>",methods=['GET','POST'])
@login_required
def g3_pl_form(reportee_id):
    reportee = [reportee_id]
    cur = mysql.connection.cursor()
    # Check if this PL owns this Reportee
    check_sql = "select * from emp_master_zoho where Emp_ID='" + str(reportee[0]) + "' and PL_ID='" + str(
        session['logged_emp_id']) + "'"
    check_validity = cur.execute(check_sql)
    if check_validity == 0:
        return 'Will you just mind your own business?'
    sql_qry = "select * from g3_self_rating where emp_id='" + str(reportee[0]) + "'"
    cur.execute(sql_qry)
    emp_ratings = cur.fetchall()
    if len(emp_ratings) == 0:
        emp_ratings = [0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0,
                       0, 0, 0, 0]
    else:
        emp_ratings = list(emp_ratings[0])

    if request.method == 'POST':
        curr_month = datetime.datetime.now()
        current_month = curr_month.strftime("%B")
        if current_month in ['July','August','September']:
            quarter = 2
        elif current_month in ['October','November','December']:
            quarter = 3
        elif current_month in ['January','February','March']:
            quarter = 4
        else:
            quarter = 1
        self_review = request.form
        emp_id = self_review['emp_id']
        on_time_task_comp = self_review['Q1_PL']
        project_mgmt_prtl_updt = self_review['Q2_PL']
        customer_exp_quality = self_review['Q3_PL']
        attendance_zoho = self_review['Q4_PL']
        reporting_expense = self_review['Q5_PL']
        project_or_daily_status = self_review['Q6_PL']
        project_documentation = self_review['Q7_PL']
        tableau_alteryx_dw = self_review['Q8_PL']
        zoho_connect = self_review['Q9_PL']
        attend_trainings = self_review['Q10_PL']
        appreciation = self_review['Q11_PL']
        opportunity = self_review['Q12_PL']
        cur = mysql.connection.cursor()
        sql_qry = "insert into pl_g3_rating values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(sql_qry,[emp_id,quarter,int(on_time_task_comp),int(project_mgmt_prtl_updt),int(customer_exp_quality),int(attendance_zoho),
                             int(reporting_expense),int(project_or_daily_status),int(project_documentation),int(tableau_alteryx_dw),
                             int(zoho_connect),int(attend_trainings),appreciation, opportunity])
        mysql.connection.commit()
        cur.close()
        return redirect('/success')
    return render_template("g3_pl_form.html", results=(reportee, emp_ratings))

@app.route("/g3_hr_form/<reportee_id>",methods=['GET','POST'])
@login_required
def g3_hr_form(reportee_id):
    # Check if HR
    if session['email'] == 'hr@crgroup.co.in':
        reportee = [reportee_id]
        # Get self rating of selected reportee started
        cur = mysql.connection.cursor()
        sql_qry = "select * from g3_self_rating where emp_id='" + str(reportee[0]) + "'"
        cur.execute(sql_qry)
        emp_ratings = cur.fetchall()
        if len(emp_ratings) == 0:
            emp_ratings = [0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0,
                           0, 0, 0, 0]
        else:
            emp_ratings = list(emp_ratings[0])
        # Get self rating of selected reportee finished
############################################################################################################
        # Get RM rating of selected reportee started
        cur = mysql.connection.cursor()
        sql_qry = "select * from rm_g3_rating where emp_id='" + str(reportee[0]) + "'"
        cur.execute(sql_qry)
        rm_ratings = cur.fetchall()
        if len(rm_ratings) == 0:
            rm_ratings = [0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0,
                            0, 0, 0, 0]
        else:
            rm_ratings = list(rm_ratings[0])
        # Get RM rating of selected reportee finished
############################################################################################################
        # Get PL rating of selected reportee started
        cur = mysql.connection.cursor()
        sql_qry = "select * from pl_g3_rating where emp_id='" + str(reportee[0]) + "'"
        cur.execute(sql_qry)
        pl_ratings = cur.fetchall()
        if len(pl_ratings) == 0:
            pl_ratings = [0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0,
                            0, 0, 0, 0]
        else:
            pl_ratings = list(pl_ratings[0])
        # Get PL rating of selected reportee finished
############################################################################################################
        # Get BH rating of selected reportee started
        cur = mysql.connection.cursor()
        sql_qry = "select * from bh_g3_rating where emp_id='" + str(reportee[0]) + "'"
        cur.execute(sql_qry)
        bh_ratings = cur.fetchall()
        if len(bh_ratings) == 0:
            bh_ratings = [0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0,
                            0, 0, 0, 0]
        else:
            bh_ratings = list(bh_ratings[0])
        # Get BH rating of selected reportee finished
##############################################################################################################
        if request.method == 'POST':
            curr_month = datetime.datetime.now()
            current_month = curr_month.strftime("%B")

            if current_month in ['July','August','September']:
                quarter = 2
            elif current_month in ['October','November','December']:
                quarter = 3
            elif current_month in ['January','February','March']:
                quarter = 4
            else:
                quarter = 1
            self_review = request.form
            emp_id = self_review['emp_id']
            on_time_task_comp = self_review['Q1_HR']
            project_mgmt_prtl_updt = self_review['Q2_HR']
            customer_exp_quality = self_review['Q3_HR']
            attendance_zoho = self_review['Q4_HR']
            reporting_expense = self_review['Q5_HR']
            project_or_daily_status = self_review['Q6_HR']
            project_documentation = self_review['Q7_HR']
            tableau_alteryx_dw = self_review['Q8_HR']
            zoho_connect = self_review['Q9_HR']
            attend_trainings = self_review['Q10_HR']
            appreciation = self_review['Q11_HR']
            opportunity = self_review['Q12_HR']
            cur = mysql.connection.cursor()
            sql_qry = "insert into hr_g3_rating values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql_qry,[emp_id,quarter,int(on_time_task_comp),int(project_mgmt_prtl_updt),int(customer_exp_quality),int(attendance_zoho),
                                 int(reporting_expense),int(project_or_daily_status),int(project_documentation),int(tableau_alteryx_dw),
                                 int(zoho_connect),int(attend_trainings),appreciation, opportunity])
            mysql.connection.commit()
            cur.close()
            return redirect('/success')
        return render_template("g3_hr_form.html", results=(reportee,emp_ratings,rm_ratings,pl_ratings,bh_ratings))
    else:
        return 'Trying to access HR data? Your mac address is now recorded and sent to hr@crgroup.co.in, do explain why you tried to hit the HR pages.'

@app.route("/g3_bh_form/<reportee_id>",methods=['GET','POST'])
@login_required
def g3_bh_form(reportee_id):
    # Check if HR
    if session['email'] == 'hsethi@crgroup.co':
        reportee = [reportee_id]
        # Get self rating of selected reportee started
        cur = mysql.connection.cursor()
        sql_qry = "select * from g3_self_rating where emp_id='" + str(reportee[0]) + "'"
        cur.execute(sql_qry)
        emp_ratings = cur.fetchall()
        if len(emp_ratings) == 0:
            emp_ratings = [0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0,
                           0, 0, 0, 0]
        else:
            emp_ratings = list(emp_ratings[0])
        # Get self rating of selected reportee finished
############################################################################################################
        # Get RM rating of selected reportee started
        cur = mysql.connection.cursor()
        sql_qry = "select * from rm_g3_rating where emp_id='" + str(reportee[0]) + "'"
        cur.execute(sql_qry)
        rm_ratings = cur.fetchall()
        if len(rm_ratings) == 0:
            rm_ratings = [0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0,
                            0, 0, 0, 0]
        else:
            rm_ratings = list(rm_ratings[0])
        # Get RM rating of selected reportee finished
############################################################################################################
        # Get PL rating of selected reportee started
        cur = mysql.connection.cursor()
        sql_qry = "select * from pl_g3_rating where emp_id='" + str(reportee[0]) + "'"
        cur.execute(sql_qry)
        pl_ratings = cur.fetchall()
        if len(pl_ratings) == 0:
            pl_ratings = [0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0,
                            0, 0, 0, 0]
        else:
            pl_ratings = list(pl_ratings[0])
        # Get PL rating of selected reportee finished
############################################################################################################

        if request.method == 'POST':
            curr_month = datetime.datetime.now()
            current_month = curr_month.strftime("%B")

            if current_month in ['July','August','September']:
                quarter = 2
            elif current_month in ['October','November','December']:
                quarter = 3
            elif current_month in ['January','February','March']:
                quarter = 4
            else:
                quarter = 1
            self_review = request.form
            emp_id = self_review['emp_id']
            on_time_task_comp = self_review['Q1_BH']
            project_mgmt_prtl_updt = self_review['Q2_BH']
            customer_exp_quality = self_review['Q3_BH']
            attendance_zoho = self_review['Q4_BH']
            reporting_expense = self_review['Q5_BH']
            project_or_daily_status = self_review['Q6_BH']
            project_documentation = self_review['Q7_BH']
            tableau_alteryx_dw = self_review['Q8_BH']
            zoho_connect = self_review['Q9_BH']
            attend_trainings = self_review['Q10_BH']
            appreciation = self_review['Q11_BH']
            opportunity = self_review['Q12_BH']
            cur = mysql.connection.cursor()
            sql_qry = "insert into bh_g3_rating values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql_qry,[emp_id,quarter,int(on_time_task_comp),int(project_mgmt_prtl_updt),int(customer_exp_quality),int(attendance_zoho),
                                 int(reporting_expense),int(project_or_daily_status),int(project_documentation),int(tableau_alteryx_dw),
                                 int(zoho_connect),int(attend_trainings),appreciation, opportunity])
            mysql.connection.commit()
            cur.close()
            return redirect('/success')
        return render_template("g3_bh_form.html", results=(reportee,emp_ratings,rm_ratings,pl_ratings))
    else:
        return 'Trying to access Business Head data? Your mac address is now recorded and sent to hr@crgroup.co.in, do explain why you tried to hit the HR pages.'


if __name__== '__main__':
    app.run(debug=True, threaded=True)