from datetime import datetime, timedelta


def calculate_range(selection):
    range_type = selection["type"]

    if range_type in (
        "all",
        "new_since_last",
        "latest_n"
    ):
        return None

    if range_type == "last_days":

        end = datetime.now()

        start = (
            end
            - timedelta(
                days=selection["days"]
            )
        )

        return start, end

    if range_type == "last_months":

        end = datetime.now()

        months = selection["months"]

        year = end.year
        month = end.month - months

        while month <= 0:
            month += 12
            year -= 1

        day = min(
            end.day,
            days_in_month(
                year,
                month
            )
        )

        start = end.replace(
            year=year,
            month=month,
            day=day
        )

        return start, end

    if range_type == "year":

        year = selection["year"]

        start = datetime(
            year,
            1,
            1
        )

        end = datetime(
            year + 1,
            1,
            1
        )

        return start, end

    if range_type == "custom":

        start = datetime.strptime(
            selection["start"],
            "%Y-%m-%d"
        )

        end = (
            datetime.strptime(
                selection["end"],
                "%Y-%m-%d"
            )
            + timedelta(days=1)
        )

        return start, end

    raise ValueError(
        f"Unknown range type: {range_type}"
    )


def days_in_month(year, month):

    if month == 12:

        next_month = datetime(
            year + 1,
            1,
            1
        )

    else:

        next_month = datetime(
            year,
            month + 1,
            1
        )

    current_month = datetime(
        year,
        month,
        1
    )

    return (
        next_month
        - current_month
    ).days


def create_filter(selection):

    range_type = selection["type"]

    if range_type in (
        "all",
        "new_since_last",
        "latest_n"
    ):
        return None

    calculated = calculate_range(
        selection
    )

    if calculated is None:
        return None

    start, end = calculated

    start_string = start.strftime(
        "%Y, %m, %d, %H, %M, %S"
    )

    end_string = end.strftime(
        "%Y, %m, %d, %H, %M, %S"
    )

    return (
        f"datetime({start_string}) <= "
        f"date < "
        f"datetime({end_string})"
    )