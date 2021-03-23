from app import app, db
from app.models import Country,update_all,daily_update, User
from db_manipulations import update_all_border_statuses, populate_db,combine_content_summary
#from timeloop import Timeloop
#from datetime import timedelta

#tl=Timeloop()

@app.shell_context_processor
def make_shell_context():
    return {'db': db,'Country':Country, 'update_all':update_all,'update_all_border_statuses':update_all_border_statuses, 'User':User, 'populate_db':populate_db,'combine_content_summary':combine_content_summary}




#@tl.job(interval=timedelta(days=1))
@app.cli.command("daily_update")
def scheduled_update():
    print("%d countries need updating" %daily_update())
    
    
#tl.start()
