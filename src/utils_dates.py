# -*- coding: utf-8 -*-
import re
from datetime import datetime

import pandas as pd


def parse_release_date(release_date):
    """从上映时间中提取首个有效日期"""
    if pd.isna(release_date):
        return None

    text = str(release_date).strip()
    if not text:
        return None

    match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if not match:
        return None

    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None
