# -*- coding: utf-8 -*-
{
    "name": "Sybyl Fleet Odoometer Report",
    "summary": """ Sybyl Fleet Odoometer Report.""",
    "author": "Sybyl",
    "website": "https://sybyl.com",
    "category": "Fleet",
    "version": "17.0.0.0",
    "depends": [
        "fleet",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/fleet_odometer_report.xml",
        "wizard/fleet_odometer.xml",
    ],
    "application": True,
    "license": "LGPL-3",
}
