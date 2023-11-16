import argparse

from dynaconf import Dynaconf

parser = argparse.ArgumentParser(description="CLI tool options")
parser.add_argument(
    "--esl-url", help="URL for the ESL service.", type=str, required=False
)
parser.add_argument(
    "--esl-port", help="Port for the ESL service.", type=int, required=False
)
parser.add_argument(
    "--esl-password", help="Password for the ESL service.", type=str, required=False
)
parser.add_argument(
    "--redis-url", help="URL for the Redis service.", type=str, required=False
)
parser.add_argument(
    "--payment-wallet", help="Wallet for payments.", type=str, required=False
)
parser.add_argument(
    "--payer-key", help="Key for payment wallet.", type=str, required=False
)


args = parser.parse_args()


settings = Dynaconf(
    envvar_prefix="REDSWITCH",
    settings_files=['settings.yaml', '.secrets.yaml'],
    **vars(args)
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
