<!--gterm notebook command=gpython-->
<p>&nbsp;

<center>
#Creating a browser-based virtual computer lab for classroom instruction</center>
</center>

<center>
##R. Saravanan

##Department of Atmospheric Sciences
</center>

<center>
![image](https://dl.dropboxusercontent.com/u/72208800/images/TAMU-logowsmall.png)
</center>

<center>
## github.com/mitotic
</center>


---

## Advantages of physical computer labs

* Uniform software

* Ability to walk around and monitor students' progress

* Students can raise a hand to request assistance

* Students can view each other's screens and collaborate

* Large files can be shared through cross-mounting




---

## Disadvantages of physical computer labs

* Hardware costs, security

* Creating user accounts, course-specific software needs

* Need root access to quickly fix problems

* Students need to be physically present to use the lab



---

## Desirable features in a virtual computer lab

* User authentication

  * *Unix login, access code, single-sign on (Google, Facebook, ...)*

* User isolation (own directories etc.)

  * *Unix accounts, Containers (Docker), Virtual machines*

* Remote access

  * *Direct HTTP port access, SSH port forwarding*

* Sharing of files, notebooks etc.

  * *Shared filesystem permissions, bundles, ...*

* Live sharing and monitoring of student progress

  * *Collaborative editing, chat, progress tracking*



---

## Current options

* Run Public IPython server

  * *Single-user with password (multi-user version planned)*

* JiffyLab

  * *A linux container for each user to run IPython Notebook server*

* Wakari (commerical, with free basic account)

  * *Cloud-based account for each user; IDE: terminal+notebook+editor*

* Sage Math Cloud

  * *Virtual machine account for each user; IDE: terminal+notebook+...*

* GraphTerm

  * *Unix account for each user; access code or Google authentication; unified terminal/notebook*


---

## Virtual lab setup using GraphTerm

Two options:

1. *Use dedicated physical server*

        sudo pip install graphterm

        gtermserver --daemon=start --auth_type=multiuser
          --user_setup=manual --users_dir=/home
          --port=80 --host=server_domain_or_ip

2. *Launch cloud instance (Amazon Web Services)*

        gtermserver --terminal --auth_type=none

        ec2launch



---

## Form interface to launch Amazon EC2 cloud instance

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-ec2launch.png)
</center>

    ec2launch --type=m3.medium --key_name=ec2key
      --ami=ami-2f8f9246 --gmail_addr=user@gmail.com
      --auth_type=multiuser --pylab --netcdf testlab



---

## User authentication

* Students use a group code to automatically create an user account

* Subsequent logins using a user-specific code or Google authentication

  * No passwords!

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-login.png)
</center>


---

## http://lab.gterm.net


<iframe width="85%" height="350" src="http://lab.gterm.net"></iframe>



---

## Terminal sharing and chat

* Instructor can view and type into students' terminal sessions any time, using URLs of the form:

        /user_name/session_name

* If groups are enabled, students in the same group can view and type into each other's terminals

* *Chat* messages from all viewers for a terminal are displayed as an overlay feed

---

### Two notebook interfaces

* Use command line notebook interface built into GraphTerm

<iframe width="85%" height="250" src="/local/demo_gnb"></iframe>

* Run IPython Notebook server for each user

<iframe width="85%" height="250" src="/local/demo_ipynb"></iframe>


---

## Lab dashboard: view students' terminals

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gadmin-terminals.png)
</center>




---

## Lab dashboard: track student progress

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gadmin-users.png)
</center>



---

### Progressively fillable notebooks

*Problem:* When and how to share answers to notebook tasks in a classroom setting?

*Solution:* Notebooks that show the correct answer automatically after you have attempted each task

<iframe width="85%" height="350" src="/local/demo_pfnb"></iframe>



---

### Progressively fillable notebook before user completes *Step 1*

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-fillable1.png)
</center>




---

### Progressively fillable notebook after user completes *Step 1*

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-fillable2.png)
</center>

---

## Some shortcomings

* Using your own cloud server is not free

  * *Standard Amazon cloud instance: $50 per month*

  * *Dedicated physical server: about same cost, but more powerful*

  * *Need good internet connectivity*

* GraphTerm client runs on Mac/Linux/Windows/Android/iOS etc., but the
  server only runs on Mac/Linux

* The notebook interface, especially the ``pylab`` mode, is very
  convenient but it shields students from some of the complexities of
  file management and program modularity

---

## Conclusions

* GraphTerm can serve as a virtual replacement for a physical computer lab

  * *Terminal sharing and chat features facilitate progress monitoring and group collaboration*

  * *Hybrid CLI-GUI interface is convenient for complex tasks like launching cloud servers and user monitoring*

* The *progressively fillable* notebook interface can provide "incremental scaffolding" and instant feedback

  * *Implement in IPython Notebook in some form?*


