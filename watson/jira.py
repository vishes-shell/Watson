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

    def jira_add_worklog(self, project, start, stop, note):
        seconds_spent = int((stop - start).total_seconds())
        worklog = self.jira_client.add_worklog(
            project, timeSpentSeconds=seconds_spent, comment=note
        )
        return worklog

    def jira_delete_worklog(self, frame):
        if frame.jira_worklog:
            self.jira_client.worklog(frame.project, frame.jira_worklog).delete()

    def stop_current(self, current, stop_at, note):
        if self.jira_track_time_required(current["project"], current["tags"]):
            worklog = self.jira_add_worklog(
                current["project"], current["start"], stop_at, note
            )
        return super().stop_current(current, stop_at, note, jira_worklog=worklog.id)
