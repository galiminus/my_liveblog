@ECHO OFF
setlocal
SET FULLPATH=
SET ALLYCOM=%FULLPATH%components\
set PYTHONPATH=%ALLYCOM%ally-api
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-authentication
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-authentication-core
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-authentication-http
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-core
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-core-http
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-core-plugin
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-core-sqlalchemy
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-http-asyncore-server
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-http-mongrel2-server
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%ally-utilities
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%support-administration
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%support-cdm
set PYTHONPATH=%PYTHONPATH%;%ALLYCOM%support-development

SET ALLYPLUG=%FULLPATH%plugins\
set PYTHONPATH=%PYTHONPATH%;%ALLYPLUG%gui-action
set PYTHONPATH=%PYTHONPATH%;%ALLYPLUG%gui-core
set PYTHONPATH=%PYTHONPATH%;%ALLYPLUG%internationalization
set PYTHONPATH=%PYTHONPATH%;%ALLYPLUG%introspection-request
set PYTHONPATH=%PYTHONPATH%;%ALLYPLUG%support-sqlalchemy

python distribution\application.py
