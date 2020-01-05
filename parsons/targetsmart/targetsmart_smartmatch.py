import logging
import requests
import uuid

logger = logging.getLogger(__name__)

# Smartmatch matching documentation can be found here:
# https://docs.targetsmart.com/my_tsmart/smartmatch/overview.html
# https://https://docs.targetsmart.com/developers/tsapis/v2/service/smartmatch.html
# The columns are heavily customized by TS, so while I would like
# to do more column validation and mapping, I'm not sure that is
# going to be possible.


class TargetSmartRequestException(Exception):
    pass


# TargetSmartConnector is not quite ideal for Targetsmart requests.
class TargetSmartApiClient(object):
    def __init__(self, api_key=None, ts_host="https://api.targetsmart.com",
                 headers=None):

        headers = headers or {}
        self.headers = {**headers, "x-api-key": api_key}
        self.ts_host = ts_host

    def request(self, api_path, method="get", headers=None, **request_kwargs):
        headers = headers or {}
        headers = {**self.headers, **headers}

        if not hasattr(requests, method):
            raise ValueError("Invalid HTTP Method. Accepts get,post")

        if not api_path.startswith("/"):
            raise ValueError("Targetsmart API path provided must lead with `/`.")

        response = getattr(requests, method)(
            self.ts_host + api_path,
            headers=headers,
            **request_kwargs
        )

        if response.status_code >= 400:
            raise TargetSmartRequestException(response.json()["error"])

        return response.json()


class TargetSmartSmartmatch(TargetSmartApiClient):
    def match(self, table, job_type, job_name=None, emails=None, call_back=None,
              **smartmatch_params):
        """
        Match a table to TargetSmart using their standard Smartmatch service.

        Args:
            table: Parsons Table Object
                A table object with the required columns. (Required columns provided by TargetSmart)
            job_type: str
                The match job type. **This is case sensitive.** (Match job names provided by TargetSmart)
            job_name: str
                Optional job name.
            emails: list
                A list of emails that will received status notifications. This
                is useful in debugging failed jobs.
            call_back: str
                A callback url to which the status will be posted. See
                `TargetSmart webhook documentation <https://https://docs.targetsmart.com/developers/tsapis/v2/service/smartmatch.html>`
                for more details.
            smartmatch_params: dict
                Optional argument according to the `TargetSmart Smartmatch documentation https://docs.targetsmart.com/developers/tsapis/v2/service/smartmatch.html`
        """ # noqa: E501,E261

        # Generate a match job
        job_name = job_name or str(uuid.uuid1())

        response = self.request(
            "/service/smartmatch",
            json={
                "filename": job_name,
                "webhook": call_back,
            }
        )

        # Upload table
        presigned_upload_url = response["url"]
        tmp_csv_file = table.to_csv()
        with open(tmp_csv_file, 'rb') as tmp_csv:
            response = requests.put(presigned_upload_url, data=tmp_csv)

        if response.status_code != 200:
            raise TargetSmartRequestException(
                "CSV Upload to presigned url failed {}".format(response.content)
            )

        logger.info(f'Table with {table.num_rows} rows uploaded to TargetSmart.')

        # TODO: Status checking, manual file retrieval separate from webhook.

