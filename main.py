import sys, click
from os import getenv, environ, execvp, path
from app import create_app, db
from app.models import User, Role
from flask_migrate import Migrate


COV = None
if environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

app = create_app(getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

# -------- Profiler --------
# from werkzeug.middleware.profiler import ProfilerMiddleware
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [30])
# --------------------------

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False, help='Run tests with coverage stats')
def test(coverage) -> None:
    if coverage and not environ.get('FLASK_COVERAGE'):
        environ['FLASK_COVERAGE'] = '1'
        execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
        COV.save()
        print('Coverage stats:')
        COV.report()
        basedir = path.abspath(path.dirname(__file__))
        covdir = path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print(f'HTML version: file://{covdir}/index.html')
        COV.erase()


# @app.cli.command()
# @click.option('--length', default=25, help='Number of function used in profiler report')
# @click.option('--profile-dir', default=None, help='Directory where report data are saved')
# def profile(length, profile_dir):
#     from werkzeug.middleware.profiler import ProfilerMiddleware
#     app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length], profile_dir=profile_dir)
#     app.run(debug=False)
