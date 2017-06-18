DEFAULT_LOGGING_SETTING =\
{
    "loggers": {
        "application_recorder": {
            "level": "DEBUG",
            "propagate": False,
            "handlers": [
                "application_file_time_handler"
            ]
        },
        "system_recorder": {
            "level": "DEBUG",
            "propagate": False,
            "handlers": [
                "console_handler",
                "system_file_size_handler"
            ]
        }
    },
    "version": 1,
    "formatters": {
        "application_formatter": {
            "format": "[%(requestid)s] [%(levelname)s] [%(asctime)s] [%(process)d:%(thread)d]\n%(message)s"
        },
        "system_formatter": {
            "format": "[%(levelname)s] [%(asctime)s] [%(process)d:%(thread)d]\n%(message)s"
        }
    },
    "disable_existing_loggers": False,
    "handlers": {
        "console_handler": {
            "formatter": "system_formatter",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        },
        "application_file_time_handler": {
            "formatter": "application_formatter",
            "backupCount": 20,
            "encoding": "utf8",
            "interval": 1,
            "when": "D",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "app.log"
        },
        "system_file_size_handler": {
            "formatter": "system_formatter",
            "backupCount": 20,
            "encoding": "utf8",
            "maxBytes": 10485760,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log"
        }
    }
}