import {RouteComponentProps} from 'react-router';
import styled from '@emotion/styled';

import Feature from 'app/components/acl/feature';
import Alert from 'app/components/alert';
import {t} from 'app/locale';
import {PageContent} from 'app/styles/organization';
import {Group, Organization} from 'app/types';
import withOrganization from 'app/utils/withOrganization';

import GroupSplitted from './groupSplitted';

type RouteParams = {groupId: Group['id']; orgId: Organization['slug']};

type Props = RouteComponentProps<RouteParams, {}> & {
  organization: Organization;
};

function GroupSplittedContainer({organization, params, location}: Props) {
  return (
    <Feature
      features={['grouping-tree-ui']}
      organization={organization}
      renderDisabled={() => (
        <PageContent>
          <Alert type="warning">{t("You don't have access to this feature")}</Alert>
        </PageContent>
      )}
    >
      <GroupSplitted
        location={location}
        groupId={params.groupId}
        organization={organization}
      />
    </Feature>
  );
}

export default withOrganization(GroupSplittedContainer);
