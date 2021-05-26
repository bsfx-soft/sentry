import React from 'react';
import styled from '@emotion/styled';

import AsyncComponent from 'app/components/asyncComponent';
import Pagination from 'app/components/pagination';
import {Panel, PanelBody, PanelHeader} from 'app/components/panels';
import {t} from 'app/locale';
import {Project} from 'app/types';
import {
  MIN_PROJECTS_FOR_PAGINATION,
  MIN_PROJECTS_FOR_SEARCH,
  NotificationSettingsByProviderObject,
  NotificationSettingsObject,
} from 'app/views/settings/account/notifications/constants';
import {
  getCurrentProviders,
  getParentField,
  groupByOrganization,
  isGroupedByProject,
} from 'app/views/settings/account/notifications/utils';
import EmptyMessage from 'app/views/settings/components/emptyMessage';
import Form from 'app/views/settings/components/forms/form';
import JsonForm from 'app/views/settings/components/forms/jsonForm';

type Props = {
  notificationType: string;
  notificationSettings: NotificationSettingsObject;
  onChange: (
    changedData: NotificationSettingsByProviderObject,
    parentId: string
  ) => NotificationSettingsObject;
} & AsyncComponent['props'];

type State = {
  projects: Project[];
} & AsyncComponent['state'];

class NotificationSettingsByProjects extends AsyncComponent<Props, State> {
  getDefaultState(): State {
    return {
      ...super.getDefaultState(),
      projects: [],
    };
  }

  getEndpoints(): ReturnType<AsyncComponent['getEndpoints']> {
    return [['projects', '/projects/']];
  }

  getProjectCount = (): number => {
    /** Check the notification settings for how many projects there are. */
    const {notificationType, notificationSettings} = this.props;

    return Object.values(notificationSettings[notificationType]?.project || {}).length;
  };

  getGroupedProjects = (): {[key: string]: Project[]} => {
    /**
     * The UI expects projects to be grouped by organization but can also use
     * this function to make a single group with all organizations.
     */
    const {projects: stateProjects} = this.state;

    return Object.fromEntries(
      Object.values(
        groupByOrganization(stateProjects)
      ).map(({organization, projects}) => [`${organization.name} Projects`, projects])
    );
  };

  getParents(): Project[] {
    /** Use the `notificationType` key to decide which parent objects to use. */
    const {projects} = this.state;

    return projects;
  }

  getParentData = (): NotificationSettingsByProviderObject => {
    /** Get a mapping of all parent IDs to the notification setting for the current providers. */
    const {notificationType, notificationSettings} = this.props;

    const provider = getCurrentProviders(notificationType, notificationSettings)[0];

    return Object.fromEntries(
      this.getParents().map(parent => [
        parent.id,
        this.getParentValues(parent.id)[provider],
      ])
    );
  };

  renderBody() {
    const {notificationType, notificationSettings, onChange} = this.props;
    const {projects, projectsPageLinks} = this.state;

    const isProject = isGroupedByProject(notificationType);
    const canSearch = this.getProjectCount() >= MIN_PROJECTS_FOR_SEARCH;
    const shouldPaginate = projects.length >= MIN_PROJECTS_FOR_PAGINATION;

    return (
      <React.Fragment>
        <Panel>
          <PanelBody>
            {canSearch && (
              <PanelHeader hasButtons={isProject}>
                <Heading>{isProject ? t('Projects') : t('Organizations')}</Heading>
                <div>
                  {isGroupedByProject(notificationType) &&
                    this.renderSearchInput({
                      stateKey: 'projects',
                      url: '/projects/',
                      placeholder: t('Search Projects'),
                    })}
                </div>
              </PanelHeader>
            )}
            <Form
              saveOnBlur
              apiMethod="PUT"
              apiEndpoint="/users/me/notification-settings/"
              initialData={this.getParentData()}
            >
              {isProject && projects.length === 0 ? (
                <EmptyMessage>{t('No projects found')}</EmptyMessage>
              ) : (
                Object.entries(this.getGroupedProjects()).map(([groupTitle, parents]) => (
                  <JsonForm
                    key={groupTitle}
                    title={groupTitle}
                    fields={parents.map(parent =>
                      getParentField(
                        notificationType,
                        notificationSettings,
                        parent,
                        onChange
                      )
                    )}
                  />
                ))
              )}
            </Form>
          </PanelBody>
        </Panel>
        {canSearch && shouldPaginate && (
          <Pagination pageLinks={projectsPageLinks} {...this.props} />
        )}
      </React.Fragment>
    );
  }
}

const Heading = styled('div')`
  flex: 1;
`;

export default NotificationSettingsByProjects;
