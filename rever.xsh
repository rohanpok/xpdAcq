$REVER_DIR = 'rever-tmp'
$ACTIVITIES = ['version_bump',
               # 'changelog',
               'tag']

$VERSION_BUMP_PATTERNS = [
    ('xpdacq/__init__.py', '__version__\s*=.*', "__version__ = '$VERSION'"),
    ]
# $CHANGELOG_FILENAME = 'CHANGELOG.rst'
# $CHANGELOG_IGNORE = ['TEMPLATE.rst']
$TAG_REMOTE = 'git@github.com:CJ-Wright/xpdAcq.git'
