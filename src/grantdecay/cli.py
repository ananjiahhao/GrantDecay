"""Command line interface for grantdecay.

Subcommands:

    surface    print the granted versus exercised permission surface per principal
    unused     print each unused-privilege finding, one per line
    report     print a grouped report of the four finding kinds
    version    print the package version

The surface, unused, and report commands take an entitlement export and an
access log export. They exit 1 when findings are present, 0 when clean.

Exit codes: 0 clean, 1 findings present, 2 usage error. argparse exits with 2 on
argument errors, which matches the standard.
