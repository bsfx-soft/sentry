export const ALL_PROVIDERS = {
  email: 'default',
  slack: 'never',
};

/** These values are stolen from the DB. */
export const VALUE_MAPPING = {
  default: 0,
  never: 10,
  always: 20,
  subscribe_only: 30,
  committed_only: 40,
};

// TODO MARCOS should these be the same?
export const MIN_PROJECTS_FOR_SEARCH = 0; // 3
export const MIN_PROJECTS_FOR_PAGINATION = 3;

export type NotificationSettingsByProviderObject = {[key: string]: string};
export type NotificationSettingsObject = {
  [key: string]: {[key: string]: {[key: string]: NotificationSettingsByProviderObject}};
};
