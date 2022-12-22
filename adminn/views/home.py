import datetime,json
from multiprocessing import managers
from tracemalloc import start
from typing import List
from unicodedata import name
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.urls import resolve
from ..models import *
from django.contrib import messages
from .email import send_forget_password_mail
import uuid
from employee.models import ChangePassword

@login_required
def home(request):
    if request.method == 'GET':
        role = Profile.objects.get(user_id=request.user.id).role
        if role == 3: 
            final_data_dict = {}
            users = User.objects.all()

            # This part is for main home page content
            date = datetime.date.today()
            start_week = date - datetime.timedelta(date.weekday()) - datetime.timedelta(7)
            end_week = start_week + datetime.timedelta(7)

            data_list_hours = {}
            data_list_minutes = {}
            queryset = UserProjectProgress.objects.filter(date__range=[start_week,end_week])

            hours, minutes = 0,0
            for flag in queryset:          
                hours,minutes = str(flag.daily_hours).split('.')
                data_list_hours[flag.userproject.project.team.name] = data_list_hours.get(flag.userproject.project.team.name, 0) + int(hours)
                data_list_minutes[flag.userproject.project.team.name] = data_list_minutes.get(flag.userproject.project.team.name, 0) + int(minutes)
        
            for key, value in data_list_minutes.items():
                data_list_hours[key] += value//60

            TeamList = TeamAndManager.objects.all()

            for i in TeamList:
                if i.name in data_list_hours.keys():
                    final_data_dict[i.name] = [i.manager.username, data_list_hours[i.name]]
                else:
                    final_data_dict[i.name] = [i.manager.username, 0]
            
            userprofile = Profile.objects.all()
            #member view start
            y = User.objects.get(username = request.user)
            x = Profile.objects.filter(user = y.id)
            #member view end

            # project button start
            project1 = Project.objects.all() 

            # project button end

            # This part is for side bar
            team_members = {}
            for team in TeamList:
                particular_team = []
                team_profiles = Profile.objects.filter(team = team)
                for i in team_profiles:
                    particular_team.append(i.user.username)
                team_members[team.name] = particular_team
            z=Profile.objects.get(user_id=request.user.id).role
                
            data = {
                'userprofile':userprofile,
                'TeamList' : TeamList,
                'TeamMembers' : team_members,
                'FinalDataDict': final_data_dict,
                'AllUsers': users,
                'x':x,

                'project1':project1,

                'role':z,

            }

            return render(request,"home.html", data)

        elif role == 2:
            team = TeamAndManager.objects.get(manager_id=request.user.id).name
            team_id = TeamAndManager.objects.get(name = team)
            team_members = Profile.objects.filter(team=team_id)
            final_dict = {}

            for team_member in team_members:
                #calculation for username and related projects
                particular_projects = UserProject.objects.filter(user=team_member.user)
                final_dict[team_member.user.username] = ["",[]]
                for project in particular_projects:
                    final_dict[team_member.user.username][0] = final_dict[team_member.user.username][0] + project.project.name + ", "
                final_dict[team_member.user.username][0] = final_dict[team_member.user.username][0][:len(final_dict[team_member.user.username][0])-2]

                #calculation for last week hours
                date = datetime.date.today()
                start_week = date - datetime.timedelta(date.weekday()) - datetime.timedelta(7)
                end_week = start_week + datetime.timedelta(7)

                data_list_hours = {}
                data_list_minutes = {}


                queryset1 = UserProjectProgress.objects.filter(userproject__in=particular_projects)
                queryset = queryset1.filter(date__range=[start_week,end_week])

                hours, minutes = 0,0

                for flag in queryset:
                    hours,minutes = str(flag.daily_hours).split('.')
                    data_list_hours[flag.userproject.user.username] = data_list_hours.get(flag.userproject.user.username, 0) + int(hours)
                    data_list_minutes[flag.userproject.user.username] = data_list_minutes.get(flag.userproject.user.username, 0) + int(minutes)

                for key, value in data_list_minutes.items():
                    data_list_hours[key] += value//60

                if team_member.user.username in data_list_hours.keys() and team_member.user.username in final_dict.keys():
                    final_dict[team_member.user.username][1].append(data_list_hours[team_member.user.username])
            
            for team_member in team_members:
                if team_member.user.username not in final_dict.keys():
                    final_dict[team_member.user.username] = ["",[]]

            TeamList = TeamAndManager.objects.all()

            z1=Profile.objects.get(user_id=request.user.id).role
            
            FinalDataDict = {
                'final_dict' : final_dict,
                'TeamList' : TeamList,
                'role1':z1,
            }
    
            return render(request,"home.html", FinalDataDict)

        else:
            employee_data_dict={}
            name1 = User.objects.get(id=request.user.id).first_name
            name2 = User.objects.get(id=request.user.id).last_name
            name= name1 + ' ' + name2
            if len(name)>1:
                name=name
            else:
                name= User.objects.get(id=request.user.id).username
            projects = UserProject.objects.filter(user_id = request.user.id).filter(project__status=1)
            employee_data_dict[name]=['','','',[]]
            if len(projects)>0:
                for i in projects:
                    employee_data_dict[name][0]=employee_data_dict[name][0]+i.project.name+','
                employee_data_dict[name][0]=employee_data_dict[name][0][:len(employee_data_dict[name][0])-1]
            else:
                employee_data_dict[name][0]='Currently on POC'
            team_name=Profile.objects.get(user=request.user.id).team.name
            employee_data_dict[name][1]=team_name
            manager_name=TeamAndManager.objects.get(name=team_name).manager
            employee_data_dict[name][2]=manager_name
            #Calculation of last week hours
            date = datetime.date.today()
            start_week = date - datetime.timedelta(date.weekday()) - datetime.timedelta(7)
            end_week = start_week + datetime.timedelta(7)

            data_list_hours = {}
            data_list_minutes = {}


            queryset1 = UserProjectProgress.objects.filter(userproject__in=projects)
            queryset = queryset1.filter(date__range=[start_week,end_week])
            hours, minutes = 0,0

            for flag in queryset:
                hours,minutes = str(flag.daily_hours).split('.')
                data_list_hours[flag.userproject.user.username] = data_list_hours.get(flag.userproject.user.username, 0) + int(hours)
                data_list_minutes[flag.userproject.user.username] = data_list_minutes.get(flag.userproject.user.username, 0) + int(minutes)
            for key, value in data_list_minutes.items():
                data_list_hours[key] += value//60

            if request.user.username in data_list_hours.keys():
                employee_data_dict[name][3]=data_list_hours[request.user.username]
            else:
                employee_data_dict[name][3]=0

            z1=Profile.objects.get(user_id=request.user.id).role
            
            max_date = str(datetime.date.today())+'T23:59'
            min_date = str(date - datetime.timedelta(date.weekday()) - datetime.timedelta(1))+'T00:00'
            default_date = str(date)+'T10:00'

            team=Profile.objects.get(user_id=request.user.id).team
            projects=Project.objects.filter(team=team)
            projects_list=[]
            for i in projects:
                if i.status == 1:
                    projects_list.append(i.name)

            FinalDataDicttt = {
                'final_dicttt' : employee_data_dict,
                'ProjectList' : projects_list,
                'min_date':min_date,
                'max_date':max_date,
                'default_date':default_date,
                'role3':z1,
            }

            return render(request,"home.html",FinalDataDicttt)

    else:
        return JsonResponse({
            "message" : "method not allowed"
        })


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/home') 
        else:
            message = 'Invalid Credentials'
            return render(request, 'login.html', {'message':message})
    if request.user.is_authenticated:
        return redirect('/home') 
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect('/')

def change_password(request,token):
    
    context={}
    try:
        profile_obj = ChangePassword.objects.get(forgot_password_token  = token)
        user_id = profile_obj.user_id
        context  = {'user_id': profile_obj.user_id}
        
        if request.method == "POST":
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")
            #user_id = request.POST.get("user_id")
            
        if user_id is None:
            messages.error(request,"No user found")
            return render(request,'change_password.html')
        
        if new_password != confirm_password:
            messages.warning(request, "Password did not matched")
            return render(request,'change_password.html')
        
        user_obj = User.objects.get(id=user_id)
        user_obj.set_password(new_password)
        user_obj.save()
        messages.success(request, "Your password has been changed")
        return redirect("/")
        
    except Exception as e:
        print(e)
    return render(request, "change_password.html",context)
            

def forgot_password(request):
   
    try:
        if request.method=="POST":
            username = request.POST.get('username')
            user_id = User.objects.get(username=username).id
            if not User.objects.filter(username=username).first():
                messages.success(request,"No User Found with this username.")
                return render(request,'forgot_password.html')
            
            user_obj = User.objects.get(username=username)
            token = str(uuid.uuid4())
            try:
                profile_obj = ChangePassword.objects.get(user=user_obj)
            except:
                profile_obj = ChangePassword(user_id=user_id)
                profile_obj.save()
            profile_obj.forgot_password_token = token
            profile_obj.save()
            send_forget_password_mail(user_obj.email,token)
            messages.success(request," Email Sent")
        return render(request,'forgot_password.html')
    except Exception as e:
        return render(request,'forgot_password.html')
    

@login_required
def AddTeam(request):
    if request.method == "POST":
        
        team = request.POST['TeamName']
        manager = request.POST.get('ManagerName')
        try:

            team_object=TeamAndManager.objects.all()
            team_list=[]
            for i in team_object:
                team_list.append(i.name)
            if team in team_list:
                messages.warning(request,(f'Team name {team} already exists. Please enter a different name'))
            else:
                new_team = TeamAndManager(name = team, manager = User.objects.get(username = manager))
                new_team.save()
                c = User.objects.get(username = manager)
                x = Profile.objects.get(user_id = c.id)
                x.role = 2
                x.save()
                messages.success(request,(f"Team {team} Added successfully.Thank You!"))
                return redirect('/home')

            
        except:
            messages.warning(request,("No user with that name. Please enter the existing user name"))
    return redirect('/home')


@login_required
def projects_list(request):
    team_projects = Project.objects.all()
    final_dictt2={}
    for project in team_projects:
        
            #calculation for last week hours
        final_dictt2[project.name]=[[],[],[],[],[]]
        final_dictt2[project.name][0]=project.team.name
        final_dictt2[project.name][1]=project.start_date
        final_dictt2[project.name][2]=project.end_date
        final_dictt2[project.name][3]=project.get_status_display()
        date = datetime.date.today()
        start_week = date - datetime.timedelta(date.weekday()) - datetime.timedelta(7)
        end_week = start_week + datetime.timedelta(7)

        data_list_hours = {}
        data_list_minutes = {}
        proj=UserProject.objects.filter(project=project.id)

        queryset1=UserProjectProgress.objects.filter(userproject__in=proj)
        queryset = queryset1.filter(date__range=[start_week,end_week])
        hours, minutes = 0,0
        for flag in queryset:
            hours,minutes = str(flag.daily_hours).split('.')
            data_list_hours[flag.userproject.project.name] = data_list_hours.get(flag.userproject.project.name, 0) + int(hours)
            data_list_minutes[flag.userproject.project.name] = data_list_minutes.get(flag.userproject.project.name, 0) + int(minutes)
        for key, value in data_list_minutes.items():
            data_list_hours[key] += value//60
        if project.name in data_list_hours.keys():
            final_dictt2[project.name][4]=data_list_hours[project.name]
        else:
            final_dictt2[project.name][4]=0
    
    for key,value in final_dictt2.items():
        print(key,"  ",value)
    z2=Profile.objects.get(user_id=request.user.id).role
    TeamList = TeamAndManager.objects.all()
    
    
    
    FinalDataDictt = {
        'final_dictt2' : final_dictt2,
        'role4':z2,
        'TeamList':TeamList,
        'team_projects' :team_projects

    }
    
    return render(request,"home.html", FinalDataDictt)
     




def newapi(request):
    filterData = request.GET["query"]
    users = User.objects.filter(Q(username__istartswith = filterData))
    ar=[]
    for i in users:
        ar.append(i.username)
    d = {
        'a' : json.dumps(ar)
    }
    return JsonResponse(d)



def searchteam(request):
    if request.method == 'GET':
        filterData1 = request.GET.get("query")
        url = request.GET["link"].split('/')[3:4]
        a=TeamAndManager.objects.all()
        b=[]
        for i in a:
            b.append(i.name)
        # users = Profile.objects.filter(Q(user__username__istartswith = filterData1))
        if url[0] in b:
            try:
                u = Profile.objects.filter(user__username__istartswith = filterData1).filter(team__name = url[0])
            except:
                pass
            if len(u) > 0:
                d = {}
                count = 0
                for i in u:
                    user_addon = {f'{count}' : f'{i.user.username}'}
                    count = count +1
                    d.update(user_addon)
            else:
                d = {
                    '0' : 'No Result Found'
                }
        else:
            team=TeamAndManager.objects.get(manager_id=request.user.id).name
            try:
                u = Profile.objects.filter(user__username__istartswith = filterData1).filter(team__name = team)
            except:
                pass
            if len(u) > 0:
                d = {}
                count = 0
                for i in u:
                    user_addon = {f'{count}' : f'{i.user.username}'}
                    count = count +1
                    d.update(user_addon)
            else:
                d = {
                    '0' : 'No Result Found'
                }
        return JsonResponse(d)
    
def searchteam_name(request):
    if request.method == 'GET':
        #filterData2 = 'p'
        filterData2 = request.GET.get("query")
        #url = request.GET["link"].split('/')[3:4]
        # users = Profile.objects.filter(Q(user__username__istartswith = filterData1))
        try:
            u = TeamAndManager.objects.filter(name__istartswith = filterData2)#.filter(team__name = url[0])
        except:
            pass
        if len(u) > 0:
            d = {}
            count = 0
            for i in u:
                team_addon = {f'{count}' : f'{i.name}'}
                count = count +1
                d.update(team_addon)
        else:
            d = {
                '0' : 'No Result Found'
            }
        return JsonResponse(d)


@login_required
def ChangeManager(request):
    if request.method == "POST":
        teamName = request.POST['teamName']
        managerName = request.POST['managerName']
        try:
            a = TeamAndManager.objects.get(name = teamName)
            old_manager_object = TeamAndManager.objects.filter(manager_id = a.manager_id)
            if len(old_manager_object) > 1:
                pass
            else:
                j = Profile.objects.get(user_id = a.manager_id)
                if j.role == 3:
                    pass
                else:
                    j.role = 1
                    j.save()
            Team_Name = TeamAndManager.objects.get(name = teamName)
            new_manager_object = User.objects.get(username = managerName)
            Team_Name.manager_id = new_manager_object.id
            Team_Name.save()
            l = Profile.objects.get(user_id = new_manager_object.id)
            l.role = 2
            l.save()
            messages.success(request,(f"Manager Successfully Changed for team {teamName}. Thank You!"))
            return redirect('/home')
        except:
            messages.error(request,("Either team name or manager name is incorrect. Please check again"))
    return redirect('/home')



@login_required
def DeleteTeam(request):
    if request.method == "POST":
        team_name = request.POST['team_name']
        try:
            delete_team = TeamAndManager.objects.get(name = team_name)
            # profile_change = Profile.objects.get(team = delete_team.id)
            n = delete_team.manager_id
            s = Profile.objects.filter(user_id = n)
            if len(s) > 1:
                pass
            else:

                m = Profile.objects.get(user_id = n)
                if m.role == 3:
                    pass
                else:
                    m.role = 1
                    m.save()
            # profile_change.delete()
            delete_team.delete()
            messages.error(request,(f"Team {delete_team.name} Deleted Successfully. Thank You!"))
        except:
            messages.error(request,f'Please select valid Team Name')
    return redirect("/home")
