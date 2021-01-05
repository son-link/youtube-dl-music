from setuptools import setup

setup(
    name="ytdl_music",
    version="0.1",
    description="Play your favorite YouTube's music videos and playlist",
    author="Alfonso Saavedra 'Son Link'",
    author_email='sonlink.dourden@gmail.com',
    license="GPL 3.0",
    url="https://son-link.github.io",
    scripts=['bin/ytdl_music'],
    packages=['ytdl_music'],
    package_dir={'ytdl_music': 'ytdl_music'},
    package_data={'ytdl_music': ['*', 'locales/*.qm']},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: Qt',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)
