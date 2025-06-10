# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/info/app_info.py
# # # Function: App information & description
# # # =======================

from decouple import config

app_title = config("APP_TITLE")
app_description = config("APP_DESCRIPTION")
app_summary = config("APP_SUMMARY")
app_version = config("APP_VERSION")
terms_of_service = config("APP_TERM_OF_SERVICE")
app_contact_name = config("APP_CONTACT_NAME")
app_contact_url = config("APP_CONTACT_URL")
app_contact_email = config("APP_CONTACT_EMAIL")
app_license_info_name = config("APP_LICENSE_INFO_NAME")
app_license_info_url = config("APP_LICENSE_INFO_URL")

dc_404 = config("DC_404")
dc_412 = config("DC_412")

usr_401_unauth = config("USR_401_UNAUTH")
usr_401_inact = config("USR_401_INACT")
usr_403 = config("USR_403")
usr_403_elders = config("USR_403_ELDERS")
usr_403_guardian = config("USR_403_GUARDIAN")
usr_403_optimus = config("USR_403_OPTIMUS")
usr_403_megatron = config("USR_403_MEGATRON")
usr_403_grimlock = config("USR_403_GRIMLOCK")
usr_403_optimus2= config("USR_403_OPTIMUS2")
usr_403_megatron2 = config("USR_403_MEGATRON2")
usr_403_grimlock2 = config("USR_403_GRIMLOCK2")

usr_409_root = config("USR_409_ROOT")
usr_409_taken = config("USR_409_TAKEN")
usr_412_uname = config("USR_412_UNAME")
usr_412_pwd = config("USR_412_PWD")
usr_412_name = config("USR_412_NAME")
usr_412_level = config("USR_412_LEVEL")
usr_412_team = config("USR_412_TEAM")

pwd_422_long = config("PWD_422_LONG")
pwd_422_all = config("PWD_422_ALL")
pwd_422_upcase = config("PWD_422_UPCASE")
pwd_422_locase = config("PWD_422_LOCASE")
pwd_422_num = config("PWD_422_NUM")
pwd_422_spc = config("PWD_422_SPC")
