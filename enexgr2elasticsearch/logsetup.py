'''
Logging helper module. Point is to setup structlog and facilitate sending to
elasticsearch directly (no logstash, fluentd, filebeat or other similar infra)

Copyright Alexandros Kosiaris 2022
'''

import logging
import sys

from logging.handlers import HTTPHandler

import ecs_logging
import structlog

def setup_logging(args):
    '''
    Setting up logging function
    '''

    # By default to stdout
    handler = logging.StreamHandler(sys.stdout)
    # Log level support
    if args.verbose == 1:
        level = logging.INFO
    elif args.verbose > 1:
        level = logging.DEBUG
    else:
        level = logging.WARN

    processors = [
            # If log level is too low, abort pipeline and throw away log entry.
            structlog.stdlib.filter_by_level,
            # Add the name of the logger to event dict.
            structlog.stdlib.add_logger_name,
            # If the "stack_info" key in the event dict is true, remove it and
            # render the current stack trace in the "stack" key.
            structlog.processors.StackInfoRenderer(),
            # If some value is in bytes, decode it to a unicode str.
            structlog.processors.UnicodeDecoder(),
            # Add callsite parameters.
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO
                ]
            ),
    ]
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        # Running in a terminal, assume dev and setup nice stuff
        processors += [
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer()
        ]
        # And we want a logging level of INFO anyway
        level = logging.INFO
    else:
        # Running under some supervisor, be more production-y
        processors += [
            # If the "exc_info" key in the event dict is either true or a
            # sys.exc_info() tuple, remove "exc_info" and render the exception
            # with traceback into the "exception" key.
            structlog.processors.format_exc_info,
        ]
        if args.ecs_logging:
            processors += [
                ecs_logging.StructlogFormatter()
            ]
            if args.ecs_logging_endpoint:
                i = args.ecs_logging_endpoint.find('/')
                host = args.ecs_logging_endpoint[:i]
                url = args.ecs_logging_endpoint[i:] + '/_doc'
                handler = ElasticSearchLogHandler(
                    host=host,
                    url=url,
                    method='POST',
                    secure=False,
                    credentials=(args.user, args.password),
                )
        else:
            processors += [
                structlog.stdlib.add_log_level,
                # Add a timestamp in ISO 8601 format.
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.KeyValueRenderer()
            ]


    logging.basicConfig(
        format="%(message)s",
        handlers=[handler],
        level=level,
    )
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class ElasticSearchLogHandler(HTTPHandler):
    '''
    Class logging to elasticsearch
    '''

    def emit(self, record):
        """
        Emit a record.
        Send the record to the web server as a application/json
        """
        try:
            msg = self.format(record)
            host = self.host
            h = self.getConnection(host, self.secure)
            url = self.url
            if self.method == "GET":
                raise ValueError("No GET please")
            h.putrequest(self.method, url)
            # support multiple hosts on one IP address...
            # need to strip optional :port from host, if present
            i = host.find(":")
            if i >= 0:
                host = host[:i]
            # See issue #30904: putrequest call above already adds this header
            # on Python 3.x.
            # h.putheader("Host", host)
            if self.method == "POST":
                h.putheader("Content-type",
                            "application/json")
                h.putheader("Content-length", str(len(msg)))
            if self.credentials:
                import base64
                s = ('%s:%s' % self.credentials).encode('utf-8')
                s = 'Basic ' + base64.b64encode(s).strip().decode('ascii')
                h.putheader('Authorization', s)
            h.endheaders()
            if self.method == "POST":
                h.send(msg.encode('utf-8'))
            h.getresponse()    #can't do anything with the result
        except Exception:
            self.handleError(record)
