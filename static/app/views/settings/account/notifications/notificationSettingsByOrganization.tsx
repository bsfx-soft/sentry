import React from 'react';

import {t} from 'app/locale';
import {OrganizationSummary} from 'app/types';
import withOrganizations from 'app/utils/withOrganizations';
import {
  NotificationSettingsByProviderObject,
  NotificationSettingsObject,
} from 'app/views/settings/account/notifications/constants';
import {getParentField} from 'app/views/settings/account/notifications/utils';
import Form from 'app/views/settings/components/forms/form';
import JsonForm from 'app/views/settings/components/forms/jsonForm';

type Props = {
  notificationType: string;
  notificationSettings: NotificationSettingsObject;
  organizations: OrganizationSummary[];
  onChange: (
    changedData: NotificationSettingsByProviderObject,
    parentId: string
  ) => NotificationSettingsObject;
};

type State = {};

class NotificationSettingsByOrganization extends React.Component<Props, State> {
  getParents(): OrganizationSummary[] {
    /** Use the `notificationType` key to decide which parent objects to use. */
    const {organizations} = this.props;

    return organizations;
  }

  render() {
    const {notificationType, notificationSettings, onChange, organizations} = this.props;

    return (
      <Form
        saveOnBlur
        apiMethod="PUT"
        apiEndpoint="/users/me/notification-settings/"
        initialData={this.getParentData()}
      >
        <JsonForm
          title={t('Organizations')}
          fields={organizations.map(organization =>
            getParentField(notificationType, notificationSettings, organization, onChange)
          )}
        />
      </Form>
    );
  }
}

export default withOrganizations(NotificationSettingsByOrganization);
