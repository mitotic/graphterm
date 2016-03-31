<!--gterm notebook command=python-->
<p>&nbsp;

<center>
#Creating a browser-based virtual computer lab for classroom instruction
</center>

<center>
##R. Saravanan

##Department of Atmospheric Sciences
</center>

<center>
![image](https://dl.dropboxusercontent.com/u/72208800/images/TAMU-logowsmall.png)
</center>

<center>
## View on GitHub: http://goo.gl/OJOkJr
</center>


---

## To view this Markdown Notebook as a slideshow

* Open it within GraphTerm

    * ``gpython $GTERM_DIR/notebooks/SciPy2014.py.gnb.md``

* Select the slide view mode (*notebook/page/slide mode*)

* Increase fontsize (*view/fontsize/xlarge*)

* Hide the terminal menubar (*view/menubar*)

* Select presentation mode of browser

* Use *Ctl-Mn* to advance and *Ctl-Mp* to go back

* Use *Ctl-C* or *Ctl-Jnqd* to quit

---

## Computer Lab *(Credit: Michael Surran/Flickr CC BY-SA 2.0)*

<center>
![image](https://dl.dropboxusercontent.com/u/72208800/images/ComputerLab-MichaelSurran-Flickr.jpg)
</center>



---

## Advantages of physical computer labs

* Uniform hardware and software

* Monitor students' progress

* Raise a hand to request assistance

* View each other's screens to collaborate

* Share files through cross-mounting



---

## Disadvantages of physical computer labs

* Hardware cost, security

* Creating user accounts, installing software

* Need root access to fix problems

* Physical presence required


---

## Background

* Climate modeler, using supercomputers to model climate change

* Taught an introductory programming course for meteorology majors for 5 years

  * IDL for the first 3 years (terminal+editor+X windows)

  * Switched to Python for last 2 years (IPython Notebooks)

* Also dabble with open-source software

  * GraphTerm, a graphical terminal interface, with a notebook mode (*SciPy 2013*)



---

## Students like to use their laptops instead of the lab computers

Can we set up a group of laptop computers to work together as a "virtual lab"?

  * Can we retain some of the advantages of a physical lab?

  * Can we go beyond the limitations of a physical lab?



---

## Desirable features in a virtual computer lab

* User authentication

<!--  * *Unix login, access code, single-sign on (Google, ...)* -->

* User isolation

<!--  * *Unix accounts, Docker, virtual machines* -->

* Remote access

<!--  * *HTTP, SSH* -->

* Sharing of files, notebooks etc.

<!--  * *Shared filesystem, bundles, ...* -->

* Live sharing and monitoring of student progress

<!--  * *Collaborative editing, chat, progress tracking* -->




---

## Current options for shared notebook environments

* Run Public IPython server

  * *Single-user with password (multi-user version planned)*

* JiffyLab

  * *A linux container for each user (Docker)*

* Wakari (commerical, with free basic account)

  * *Cloud-based; IDE: terminal+notebook+editor*

* Sage Math Cloud

  * *Virtual machine account; IDE: terminal+notebook+...*


---

## Why not extend GraphTerm to support a virtual computer lab?

Students access GraphTerm server on a remote computer

* Automatically create Unix account for each student

* Access code or Google authentication


Students had a choice of the following:

* Run public IPython Notebook server

* Use GraphTerm's built-in lightweight notebook interface

  * Shares collaborative features of terminal

  * Compatible with IPython Notebook (``*.ipynb``)



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

## User authentication

* Students use a group code to automatically create an user account

* Subsequent logins using a user-specific code or Google authentication

  * No passwords!

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-login.png)
</center>



---

## Try it out at http://lab.gterm.net


<iframe width="85%" height="350" src="http://lab.gterm.net"></iframe>




---

## Terminal sharing and chat

* Instructor can view students' terminal sessions any time, using URLs of the form:

        /user_name/session_name

* For group projects, students in the same group can access each other's terminals

* *Chat* messages from all viewers for a terminal are displayed as an overlay feed


---

### Two notebook interfaces

* Use command line notebook interface built into GraphTerm

<iframe width="85%" height="250" src="/local/demo_gnb"></iframe>

* Run IPython Notebook server for each user

<iframe width="85%" height="250" src="/local/demo_ipynb"></iframe>



---

## Lab dashboard: track student progress

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gadmin-users.png)
</center>




---

## Lab dashboard: view students' terminals

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gadmin-terminals.png)
</center>





---

### *Progressively fillable* notebooks

*Problem:* When and how to share answers to notebook tasks in a
classroom setting?

*Solution:* Notebooks that display the correct answer automatically
after you have attempted each task. Allow students to continue working
on interacting pieces of code, even if they get a piece wrong early
on.

Steps:

* First code cell is displayed, with key lines redacted out. Also displayed are:

  * Any preceding Markdown cells

  * Expected output of the correct code execution (text or graphics)

* Student types code and executes it using Control-Enter

* After some tries, type Shift-Enter to display and execute correct code

  * Last code attempt and associated output are also displayed

* Next code cell (and associated Markdown) are displayed

* Repeat ...


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

### Progressively fillable notebook live demo

<iframe width="85%" height="400" src="/local/demo_pfnb"></iframe>


---

## Form interface to launch Amazon EC2 cloud instance

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-ec2launch.png)
</center>

    ec2launch --type=m3.medium --key_name=ec2key
      --ami=ami-2f8f9246 --gmail_addr=user@gmail.com
      --auth_type=multiuser --pylab --netcdf testlab




---

## Clickable interface to manage Amazon EC2 cloud instances

<center>
![image](https://github.com/mitotic/graphterm/raw/master/doc-images/gt-ec2list.png)
</center>

    ec2list


---

## Some shortcomings

* Using your own cloud server is not free

  * Standard Amazon cloud instance: $50 per month

  * Dedicated physical server: about same cost, but more powerful

  * Need good internet connectivity

* GraphTerm client runs on Mac/Linux/Windows/Android/iOS etc., but the
  server only runs on Mac/Linux

* The notebook interface, especially the ``pylab`` mode, is very
  convenient but it shields students from some of the complexities of
  file management and program modularity


---

## Conclusions

* A virtual computer lab can duplicate some of the advantages of a physical computer lab

  * Terminal sharing and chat features for tracking progress and collaboration

  * Hybrid CLI-GUI interface for complex tasks like launching servers and user monitoring

* A virtual lab can boldy go where no physical lab has gone before

  * No physical presence required! Always available!

  * *Progressively fillable* notebook assignments for "incremental scaffolding" and instant feedback

    * Implement a variant in IPython Notebook?

## github.com/mitotic/graphterm

## http://goo.gl/OJOkJr

