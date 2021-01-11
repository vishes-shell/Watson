import re

from jira import JIRA, Worklog
from watson.watson import ConfigurationError


class JiraMixin:
    @property
    def jira_enabled(self) -> bool:
        return self.config.getboolean("jira", "enabled", default=False)

    def jira_track_time_required(self, project, tags, **kwargs) -> bool:
        config = self.config

        if not self.jira_enabled:
            return False

        project_regex = config.get("jira", "project_regex")
        track_time_tag = config.get("jira", "track_time_tag", default="track-time")

        if not project_regex:
            raise ConfigurationError(
                "You must specify jira.project_regex in order to use jira integration"
            )

        project_jira_related = re.match(project_regex, project)
        return bool(project_jira_related and track_time_tag in tags)

    @property
    def jira_client(self) -> JIRA:
        config = self.config

        server = config.get("jira", "server")
        user = config.get("jira", "user")
        token = config.get("jira", "token")

        if self.jira_enabled and not all((server, user, token)):
            raise ConfigurationError(
                "You must specify jira.server, jira.user and jira.token "
                "in order to use jira integration"
            )

        return JIRA(server, basic_auth=(user, token))

    def jira_add_worklog(self, project, start, stop, comment=None):
        seconds_spent = int((stop - start).total_seconds())
        worklog = self.jira_client.add_worklog(
            project, timeSpentSeconds=seconds_spent, comment=comment
        )
        return worklog

    def jira_delete_worklog(self, frame):
        if frame.jira_worklog:
            self.jira_client.worklog(frame.project, frame.jira_worklog).delete()

    def stop_current(self, current, stop_at, note):
        stop_kwargs = {"current": current, "stop_at": stop_at, "note": note}

        if self.jira_track_time_required(current["project"], current["tags"]):
            review_tag = self.config.get("jira", "review_tag", default="review")

            comment = None
            if review_tag in current["tags"]:
                comment = self.config.get("jira", "review_comment", default="review")

            worklog = self.jira_add_worklog(
                current["project"], current["start"], stop_at, comment=comment
            )
            stop_kwargs["jira_worklog"] = worklog.id

        return super().stop_current(**stop_kwargs)
