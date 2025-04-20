<!-- src/views/Settings.vue -->
<template>
  <div class="settings-page">
    <v-card>
      <v-card-title>
        <h1>{{ $t('settings.title') }}</h1>
      </v-card-title>
      
      <v-card-text>
        <v-alert
          v-if="isFirstStart"
          type="info"
          variant="outlined"
          icon="mdi-hand-wave"
          prominent
          class="mb-4"
        >
          <h3 class="text-h5 mb-2">{{ $t('settings.welcomeMessage') }}</h3>
          <p>{{ $t('settings.firstTimeInstructions') }}</p>
        </v-alert>
        <v-alert v-if="showSuccessAlert" type="success" closable>
          {{ $t('settings.saveSuccess') }}
        </v-alert>
        
        <v-alert v-if="showErrorAlert" type="error" closable>
          {{ $t('settings.saveError') }}: {{ errorMessage }}
        </v-alert>

        <v-form ref="form" v-model="valid">
          <!-- Tabs für verschiedene Einstellungskategorien -->
          <v-tabs v-model="activeTab">
            <v-tab value="general">{{ $t('settings.general') }}</v-tab>
            <v-tab value="servers">{{ $t('settings.servers') }}</v-tab>
            <v-tab value="email">{{ $t('settings.email') }}</v-tab>
            <v-tab value="ldap">{{ $t('settings.ldap') }}</v-tab>
            <v-tab value="users">{{ $t('settings.users') }}</v-tab>
            <v-tab value="selectors">{{ $t('settings.selectors') }}</v-tab>
          </v-tabs>

          <v-window v-model="activeTab">
            <!-- Allgemeine Einstellungen -->
            <v-window-item value="general">
              <v-container>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="settings.general.defaultLanguage"
                      :items="languageOptions"
                      :label="$t('settings.defaultLanguage')"
                    ></v-select>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="settings.general.defaultTheme"
                      :items="themeOptions"
                      :label="$t('settings.defaultTheme')"
                    ></v-select>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="settings.general.defaultTemplate"
                      :items="templateOptions"
                      :label="$t('settings.defaultTemplate')"
                      :loading="loadingTemplates"
                    ></v-select>
                  </v-col>
                </v-row>
              </v-container>
            </v-window-item>

            <!-- Server-Tab -->
            <v-window-item value="servers">
              <v-container>
                <v-alert v-if="isFirstStart || !servers.length" type="info" variant="outlined" class="mb-4">
                  <h3 class="text-h5 mb-2">{{ $t('settings.serverSetupInfo') }}</h3>
                  <p>{{ $t('settings.serverSetupInstructions') }}</p>
                </v-alert>
                
                <!-- Server-Verwaltung -->
                <v-card>
                  <v-card-title>
                    {{ $t('settings.serverManagement') }}
                    <v-spacer></v-spacer>
                    <v-btn 
                      color="primary" 
                      @click="openServerDialog(null)"
                      :disabled="!isAdmin"
                    >
                      <v-icon start>mdi-server-plus</v-icon>
                      {{ $t('settings.addServer') }}
                    </v-btn>
                  </v-card-title>
                  
                  <v-data-table
                    :headers="serverHeaders"
                    :items="servers"
                    :loading="loadingServers"
                    :items-per-page="10"
                  >
                    <template v-slot:item.status="{ item }">
                      <v-icon :color="item.status === 'connected' ? 'success' : (item.status === 'error' ? 'error' : 'warning')">
                        {{ item.status === 'connected' ? 'mdi-lan-connect' : 'mdi-lan-disconnect' }}
                      </v-icon>
                      <!--
                      <v-chip
                        :color="item.status === 'connected' ? 'success' : (item.status === 'error' ? 'error' : 'warning')"
                        size="small"
                      >
                        {{ item.status === 'connected' ? $t('common.connected') : 
                          (item.status === 'error' ? $t('common.error') : $t('common.unknown')) }}
                      </v-chip>
                      -->
                    </template>

                    <template v-slot:item.is_default="{ item }">
                      <v-chip
                        :color="item.is_default ? 'primary' : 'grey'"
                        size="small"
                        label
                        text-color="white"
                      >
                        {{ item.is_default ? $t('settings.defaultServer') : $t('settings.additionalServer') }}
                      </v-chip>
                    </template>
                    
                    <template v-slot:item.actions="{ item }">
                      <v-btn
                        icon="mdi-pencil"
                        size="small"
                        @click="openServerDialog(item)"
                        :disabled="!isAdmin"
                        :title="$t('common.edit')"
                      ></v-btn>
                      
                      <v-btn
                        icon="mdi-connection"
                        size="small"
                        @click="testServerConnection(item)"
                        :disabled="!isAdmin"
                        :title="$t('settings.testConnection')"
                      ></v-btn>
                      
                      <v-btn
                        icon="mdi-star"
                        size="small"
                        @click="setDefaultServer(item)"
                        :disabled="!isAdmin || item.is_default"
                        :title="$t('settings.setAsDefault')"
                      ></v-btn>
                      
                      <v-btn
                        icon="mdi-delete"
                        size="small"
                        @click="confirmDeleteServer(item)"
                        :disabled="!isAdmin || item.is_default || servers.length <= 1"
                        :title="$t('common.delete')"
                      ></v-btn>
                    </template>
                  </v-data-table>
                </v-card>
              </v-container>
            </v-window-item>

            <!-- E-Mail Einstellungen -->
            <v-window-item value="email">
              <v-container>
                <!-- Email provider selection -->
                <v-row>
                  <v-col cols="12">
                    <v-radio-group v-model="settings.email.useGraphAPI" inline>
                      <v-radio :label="$t('settings.emailProviderSmtp')" :value="false"></v-radio>
                      <v-radio :label="$t('settings.emailProviderGraph')" :value="true"></v-radio>
                    </v-radio-group>
                  </v-col>
                </v-row>

                <!-- SMTP Settings -->
                <div v-if="!settings.email.useGraphAPI">
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.server"
                        :label="$t('settings.smtpServer')"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.port"
                        :label="$t('settings.smtpPort')"
                        type="number"
                      ></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.username"
                        :label="$t('settings.smtpUsername')"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.password"
                        :label="$t('settings.smtpPassword')"
                        :append-icon="showSmtpPassword ? 'mdi-eye-off' : 'mdi-eye'"
                        :type="showSmtpPassword ? 'text' : 'password'"
                        @click:append="showSmtpPassword = !showSmtpPassword"
                      ></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.sender"
                        :label="$t('settings.emailSender')"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-switch
                        v-model="settings.email.useTLS"
                        :label="$t('settings.useTLS')"
                      ></v-switch>
                    </v-col>
                  </v-row>
                  <v-row v-if="settings.email.useTLS">
                    <v-col cols="12">
                      <v-alert
                        type="info"
                        variant="outlined"
                      >
                        {{ $t('settings.tlsInfo') }}
                      </v-alert>
                    </v-col>
                  </v-row>
                </div>
                
                <!-- Microsoft Graph API Settings -->
                <div v-if="settings.email.useGraphAPI">
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.tenantId"
                        :label="$t('settings.graphTenantId')"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.clientId"
                        :label="$t('settings.graphClientId')"
                      ></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.clientSecret"
                        :label="$t('settings.graphClientSecret')"
                        :append-icon="showGraphSecret ? 'mdi-eye-off' : 'mdi-eye'"
                        :type="showGraphSecret ? 'text' : 'password'"
                        @click:append="showGraphSecret = !showGraphSecret"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.userEmail"
                        :label="$t('settings.graphUserEmail')"
                      ></v-text-field>
                    </v-col>                    
                    <v-col cols="12">
                      <v-switch
                        v-model="settings.email.verifyCertGraphAPI"
                        :label="$t('settings.graphVerifyCert')"
                      ></v-switch>
                    </v-col>
                    <v-col cols="12">
                      <v-switch
                        v-model="settings.email.useProxy"
                        :label="$t('settings.useProxy')"
                      ></v-switch>
                    </v-col>
                  </v-row>
                  <v-row v-if="settings.email.useProxy">
                    <v-col cols="12">
                      <v-divider class="my-4"></v-divider>
                      <h4 class="text-subtitle-1">{{ $t('settings.proxySettings') }}</h4>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.proxyUrl"
                        :label="$t('settings.proxyUrl')"
                        :hint="$t('settings.proxyUrlHint')"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model.number="settings.email.proxyPort"
                        :label="$t('settings.proxyPort')"
                        type="number"
                        :hint="$t('settings.proxyPortHint')"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.proxyUser"
                        :label="$t('settings.proxyUser')"
                        :hint="$t('settings.proxyOptional')"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="settings.email.proxyPassword"
                        :label="$t('settings.proxyPassword')"
                        :append-icon="showProxyPassword ? 'mdi-eye-off' : 'mdi-eye'"
                        :type="showProxyPassword ? 'text' : 'password'"
                        :hint="$t('settings.proxyOptional')"
                        @click:append="showProxyPassword = !showProxyPassword"
                      ></v-text-field>
                    </v-col>
                  </v-row>
                </div>

                <v-row>
                  <v-col cols="12">
                    <v-btn 
                      color="primary" 
                      @click="testEmailSettings"
                      :loading="testingEmail"
                    >
                      {{ $t('settings.testEmailSettings') }}
                    </v-btn>
                    
                    <v-alert
                      v-if="emailTestResult !== null"
                      :type="emailTestResult.success ? 'success' : 'error'"
                      class="mt-3"
                      closable
                    >
                      {{ emailTestResult.message }}
                    </v-alert>
                  </v-col>
                </v-row>
              </v-container>
            </v-window-item>

            <!-- LDAP Einstellungen -->
            <v-window-item value="ldap">
              <v-container>
                <v-row>
                  <v-col cols="12">
                    <v-switch
                      v-model="settings.ldap.enabled"
                      :label="$t('settings.ldapEnabled')"
                    ></v-switch>
                  </v-col>
                </v-row>
                  
                <v-row v-if="settings.ldap.enabled">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.server"
                      :label="$t('settings.ldapServer')"
                      :hint="$t('settings.ldapServerHint')"
                    ></v-text-field>
                  </v-col>
                    
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="settings.ldap.port"
                      type="number"
                      :label="$t('settings.ldapPort')"
                      :hint="$t('settings.ldapPortHint')"
                    ></v-text-field>
                  </v-col>
                </v-row>
                  
                <v-row v-if="settings.ldap.enabled">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.bindDN"
                      :label="$t('settings.ldapBindDN')"
                      :hint="$t('settings.ldapBindDNHint')"
                    ></v-text-field>
                  </v-col>
                    
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.bindPassword"
                      :label="$t('settings.ldapBindPassword')"
                      :append-icon="showLdapPassword ? 'mdi-eye-off' : 'mdi-eye'"
                      :type="showLdapPassword ? 'text' : 'password'"
                      @click:append="showLdapPassword = !showLdapPassword"
                    ></v-text-field>
                  </v-col>
                </v-row>
                  
                <v-row v-if="settings.ldap.enabled">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.searchBase"
                      :label="$t('settings.ldapSearchBase')"
                      :hint="$t('settings.ldapSearchBaseHint')"
                    ></v-text-field>
                  </v-col>
                    
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.searchFilter"
                      :label="$t('settings.ldapSearchFilter')"
                      :hint="$t('settings.ldapSearchFilterHint')"
                    ></v-text-field>
                  </v-col>
                </v-row>
                  
                <v-row v-if="settings.ldap.enabled">
                  <v-col cols="12" md="6">
                    <v-switch
                      v-model="settings.ldap.tlsEnabled"
                      :label="$t('settings.ldapTlsEnabled')"
                    ></v-switch>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-switch
                      v-model="settings.ldap.useSSL"
                      :label="$t('settings.ldapSslEnabled')"
                    ></v-switch>
                  </v-col>
                </v-row>

                <v-row v-if="settings.ldap.enabled">
                  <v-col cols="12" md="6">
                    <v-switch
                      v-model="settings.ldap.verifyCertLDAP"
                      :label="$t('settings.ldapVerifyCert')"
                    ></v-switch>
                  </v-col>
                </v-row>

                <v-divider class="my-4" v-if="settings.ldap.enabled"></v-divider>
                <h3 class="text-subtitle-1 mb-2" v-if="settings.ldap.enabled">{{ $t('settings.ldapGroupMapping') }}</h3>
                  
                <v-row v-if="settings.ldap.enabled">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.groupSearchBase"
                      :label="$t('settings.ldapGroupSearchBase')"
                      :hint="$t('settings.ldapGroupSearchBaseHint')"
                    ></v-text-field>
                  </v-col>
                    
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.groupSearchFilter"
                      :label="$t('settings.ldapGroupSearchFilter')"
                      :hint="$t('settings.ldapGroupSearchFilterHint')"
                    ></v-text-field>
                  </v-col>
                </v-row>
                  
                <v-row v-if="settings.ldap.enabled">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.groupRoleAttribute"
                      :label="$t('settings.ldapGroupRoleAttribute')"
                      :hint="$t('settings.ldapGroupRoleAttributeHint')"
                    ></v-text-field>
                  </v-col>
                    
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="settings.ldap.adminGroupName"
                      :label="$t('settings.ldapAdminGroupName')"
                      :hint="$t('settings.ldapAdminGroupNameHint')"
                    ></v-text-field>
                  </v-col>
                </v-row>
                  
                <v-row v-if="settings.ldap.enabled">
                  <v-col cols="12">
                    <v-btn 
                      color="primary"
                      @click="testLdapConnection"
                      :loading="testingLdap"
                    >
                      {{ $t('settings.testLdapConnection') }}
                    </v-btn>
                      
                    <v-alert
                      v-if="ldapTestResult !== null"
                      :type="ldapTestResult.success ? 'success' : 'error'"
                      class="mt-3"
                      closable
                    >
                      {{ ldapTestResult.message }}
                    </v-alert>
                  </v-col>
                </v-row>
              </v-container>
            </v-window-item>

            <!-- Benutzer Tab -->
            <v-window-item value="users">
              <v-container>
                <!-- Benutzerliste -->
                <v-card>
                  <v-card-title>
                    {{ $t('settings.userManagement') }}
                    <v-spacer></v-spacer>
                    <v-btn 
                      color="primary" 
                      @click="openUserDialog(null)"
                      :disabled="!isAdmin"
                    >
                      <v-icon start>mdi-account-plus</v-icon>
                      {{ $t('settings.addUser') }}
                    </v-btn>
                  </v-card-title>
                  
                  <v-data-table
                    :headers="userHeaders"
                    :items="users"
                    :loading="loadingUsers"
                    :items-per-page="10"
                  >
                    <template v-slot:item.is_admin="{ item }">
                      <v-chip
                        :color="item.is_admin ? 'primary' : 'grey'"
                        size="small"
                        label
                        text-color="white"
                      >
                        {{ item.is_admin ? $t('settings.roleAdmin') : $t('settings.roleUser') }}
                      </v-chip>
                    </template>
                    
                    <template v-slot:item.auth_type="{ item }">
                      {{ item.auth_type || 'internal' }}
                    </template>
                    
                    <template v-slot:item.created="{ item }">
                      {{ formatDate(item.created) }}
                    </template>
                    
                    <template v-slot:item.actions="{ item }">
                      <v-btn
                        icon="mdi-pencil"
                        size="small"
                        @click="openUserDialog(item)"
                        :disabled="!isAdmin"
                      ></v-btn>
                      
                      <v-btn
                        icon="mdi-delete"
                        size="small"
                        @click="confirmDeleteUser(item)"
                        :disabled="!isAdmin || isLastAdmin(item) || isCurrentUser(item)"
                      ></v-btn>
                    </template>
                  </v-data-table>
                </v-card>
              </v-container>
            </v-window-item>

            <!-- Grafana Selektoren Tab -->
            <v-window-item value="selectors">
              <v-container>
                <v-card>
                  <v-card-title>
                    {{ $t('settings.selectorsManagement') }}
                    <v-spacer></v-spacer>
                    <v-btn 
                      color="primary" 
                      @click="addSelector"
                      :disabled="!isAdmin"
                    >
                      <v-icon start>mdi-plus</v-icon>
                      {{ $t('settings.addSelector') }}
                    </v-btn>
                  </v-card-title>
                  
                  <v-data-table
                    :headers="selectorHeaders"
                    :items="settings.grafana_selectors || []"
                    :loading="loadingSelectors"
                    :items-per-page="10"
                  >
                    <template v-slot:item.actions="{ item }">
                      <v-btn
                        icon="mdi-pencil"
                        size="small"
                        @click="editSelector(item)"
                        :disabled="!isAdmin"
                        :title="$t('common.edit')"
                      ></v-btn>
                      
                      <v-btn
                        icon="mdi-delete"
                        size="small"
                        @click="confirmDeleteSelector(item)"
                        :disabled="!isAdmin"
                        :title="$t('common.delete')"
                      ></v-btn>
                    </template>
                  </v-data-table>
                </v-card>
              </v-container>
            </v-window-item>
          </v-window>
        </v-form>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions>
        <v-btn 
          variant="text"
          color="info" 
          @click="applySettings"
          :loading="applying"
        >
          <v-icon start>mdi-refresh</v-icon>
          {{ $t('settings.applySettings') }}
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn 
          color="primary" 
          @click="saveSettings"
          :loading="saving"
          :disabled="!valid"
        >
          <v-icon start>mdi-content-save</v-icon>
          {{ $t('common.save') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  
    <!-- User Dialog -->
    <v-dialog v-model="userDialog.show" max-width="600px">
      <v-card>
        <v-card-title>
          {{ userDialog.isEdit ? $t('settings.editUser') : $t('settings.addUser') }}
        </v-card-title>
        
        <v-card-text>
          <v-form ref="userForm" v-model="userDialog.valid">
            <v-text-field
              v-model="userDialog.data.username"
              :label="$t('settings.username')"
              :disabled="userDialog.isEdit"
              :rules="userDialog.isEdit ? [] : [v => !!v || $t('settings.usernameRequired')]"
              required
            ></v-text-field>
            
            <v-text-field
              v-model="userDialog.data.display_name"
              :label="$t('settings.displayName')"
            ></v-text-field>
            
            <v-text-field
              v-model="userDialog.data.password"
              :label="$t('settings.password')"
              :placeholder="userDialog.isEdit ? $t('settings.leaveEmptyToKeep') : ''"
              :rules="userDialog.isEdit ? [] : [v => !!v || $t('settings.passwordRequired')]"
              :type="showUserPassword ? 'text' : 'password'"
              :append-icon="showUserPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append="showUserPassword = !showUserPassword"
            ></v-text-field>
            
            <v-switch
              v-model="userDialog.data.is_admin"
              :label="$t('settings.isAdmin')"
              :disabled="userDialog.isEdit && isLastAdmin(userDialog.data) && userDialog.data.is_admin"
            ></v-switch>

            <v-select
              v-model="userDialog.data.auth_type"
              :items="authTypeOptions"
              :label="$t('settings.authType')"
            ></v-select>
          </v-form>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="userDialog.show = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn 
            color="primary" 
            @click="saveUser"
            :disabled="!userDialog.valid || userSaving"
            :loading="userSaving"
          >
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Server-Dialog -->
    <v-dialog v-model="serverDialog.show" max-width="600px">
      <v-card>
        <v-card-title>
          {{ serverDialog.isEdit ? $t('settings.editServer') : $t('settings.addServer') }}
        </v-card-title>
        
        <v-card-text>
          <v-form ref="serverForm" v-model="serverDialog.valid">
            <v-text-field
              v-model="serverDialog.data.name"
              :label="$t('settings.serverName')"
              :rules="[v => !!v || $t('settings.serverNameRequired')]"
              required
            ></v-text-field>
            
            <v-text-field
              v-model="serverDialog.data.url"
              :label="$t('settings.serverUrl')"
              :rules="[v => !!v || $t('settings.serverUrlRequired')]"
              hint="http://grafana.example.com:3000"
              persistent-hint
              required
            ></v-text-field>
            
            <v-text-field
              v-model="serverDialog.data.username"
              :label="$t('settings.serverUsername')"
              :rules="[v => !!v || $t('settings.serverUsernameRequired')]"
              required
            ></v-text-field>
            
            <v-text-field
              v-model="serverDialog.data.password"
              :label="$t('settings.serverPassword')"
              :placeholder="serverDialog.isEdit ? $t('settings.leaveEmptyToKeep') : ''"
              :rules="serverDialog.isEdit ? [] : [v => !!v || $t('settings.serverPasswordRequired')]"
              :type="showServerPassword ? 'text' : 'password'"
              :append-icon="showServerPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append="showServerPassword = !showServerPassword"
            ></v-text-field>
            
            <v-switch
              v-model="serverDialog.data.is_default"
              :label="$t('settings.serverIsDefault')"
              :disabled="serverDialog.isEdit && serverDialog.data.is_default"
            ></v-switch>
          </v-form>
          
          <v-alert
            v-if="serverTestResult"
            :type="serverTestResult.success ? 'success' : 'error'"
            class="mt-3"
            closable
          >
            {{ serverTestResult.message }}
          </v-alert>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="serverDialog.show = false">
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn 
            color="primary" 
            @click="saveServer"
            :disabled="!serverDialog.valid"
          >
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Selektor Dialog -->
    <v-dialog v-model="selectorDialog.show" max-width="600px">
      <v-card>
        <v-card-title>
          {{ selectorDialog.isEdit ? $t('settings.editSelector') : $t('settings.addSelector') }}
        </v-card-title>
        
        <v-card-text>
          <v-form ref="selectorForm" v-model="selectorDialog.valid">
            <v-text-field
              v-model="selectorDialog.data.version"
              :label="$t('settings.selectorVersion')"
              :rules="[v => !!v || $t('settings.selectorVersionRequired')]"
              :hint="$t('settings.selectorVersionHint')"
              persistent-hint
              required
            ></v-text-field>
            
            <v-text-field
              v-model="selectorDialog.data.selector"
              :label="$t('settings.selectorValue')"
              :rules="[v => !!v || $t('settings.selectorValueRequired')]"
              :hint="$t('settings.selectorValueHint')"
              persistent-hint
              required
            ></v-text-field>
          </v-form>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="selectorDialog.show = false">
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn 
            color="primary" 
            @click="saveSelector"
            :disabled="!selectorDialog.valid"
          >
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/index'
import { useAuthStore } from '@/stores/auth'
import { emitter } from '@/plugins/emitter'
import { storeToRefs } from 'pinia'

const i18n = useI18n()
const appStore = useAppStore()
const authStore = useAuthStore()
const { user } = storeToRefs(authStore)
const { servers } = storeToRefs(appStore)
const loadingServers = ref(false)
const serverForm = ref(null)
const showServerPassword = ref(false)
const serverTestResult = ref(null)
const serverHeaders = ref([])

// Reactive state
const form = ref(null)
const userForm = ref(null)
const valid = ref(true)
const activeTab = ref('general')
const saving = ref(false)
const showSuccessAlert = ref(false)
const showErrorAlert = ref(false)
const errorMessage = ref('')
const showSmtpPassword = ref(false)
const testingEmail = ref(false)
const emailTestResult = ref(null)
const loadingTemplates = ref(false)
const applying = ref(false)
const isFirstStart = ref(false)
const showGraphSecret = ref(false)
const showProxyPassword = ref(false)
const authTypeOptions = ref([
  { title: 'Internal', value: 'internal' },
  { title: 'LDAP', value: 'LDAP' }
])
const showLdapPassword = ref(false)
const testingLdap = ref(false)
const ldapTestResult = ref(null)
const showUserPassword = ref(false)
const loadingUsers = ref(false)
const userSaving = ref(false)
const users = ref([])
const userHeaders = ref([])

// Computed properties
const isAdmin = computed(() => user.value && user.value.is_admin)

// Dialog state
const userDialog = reactive({
  show: false,
  isEdit: false,
  valid: true,
  data: {
    username: '',
    display_name: '',
    password: '',
    is_admin: false,
    auth_type: 'internal'
  }
})

// Form options
const languageOptions = ref([
  { title: 'Deutsch', value: 'de' },
  { title: 'English', value: 'en' }
])

const themeOptions = ref([
  { title: 'Dark', value: 'dark' },
  { title: 'Light', value: 'light' }
])

const templateOptions = ref([])

// Settings object
const settings = reactive({
  general: {
    defaultLanguage: 'de',
    defaultTheme: 'dark',
    defaultTemplate: 'default',
  },
  grafana_selectors: [],
  grafana: {
    url: '',
    username: '',
    password: '',
  },
  email: {
    server: '',
    port: 587,
    username: '',
    password: '',
    sender: '',
    useTLS: true,
    useGraphAPI: false,
    clientId: '',
    clientSecret: '',
    tenantId: '',
    userEmail: '',
    verifyCertGraphAPI: true,
    useProxy: false,
    proxyUrl: '',
    proxyPort: '',
    proxyUser: '',
    proxyPassword: ''
  },
  ldap: {
    enabled: false,
    server: '',
    port: 389,
    bindDN: '',
    bindPassword: '',
    searchBase: '',
    searchFilter: '(uid=%u)',
    tlsEnabled: false,
    useSSL: false,
    verifyCertLDAP: true,
    groupSearchBase: '',
    groupSearchFilter: '(member=%D)',
    groupRoleAttribute: 'cn',
    adminGroupName: 'grafana-admins'
  }
})

const serverDialog = reactive({
  show: false,
  isEdit: false,
  valid: true,
  data: {
    id: '',
    name: '',
    url: '',
    username: '',
    password: '',
    is_default: false
  }
})

// Methods
const updateUserHeaders = () => {
  userHeaders.value = [
    { title: i18n.t('settings.username'), key: 'username' },
    { title: i18n.t('settings.displayName'), key: 'display_name' },
    { title: i18n.t('settings.role'), key: 'is_admin' },
    { title: i18n.t('settings.authType'), key: 'auth_type' },
    { title: i18n.t('settings.created'), key: 'created' },
    { title: i18n.t('common.actions'), key: 'actions', sortable: false }
  ]
}

const updateServerHeaders = () => {
  serverHeaders.value = [
    { title: i18n.t('settings.serverName'), key: 'name' },
    { title: i18n.t('settings.serverUrl'), key: 'url' },
    { title: i18n.t('settings.serverUsername'), key: 'username' },
    { title: i18n.t('common.status'), key: 'status' },
    { title: i18n.t('settings.serverDefault'), key: 'is_default' },
    { title: i18n.t('common.actions'), key: 'actions', sortable: false }
  ]
}

const fetchServers = async () => {
  loadingServers.value = true
  try {
    await appStore.fetchServers()
  } catch (error) {
    console.error('Error fetching servers:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.errorFetchingServers')}: ${error.message || i18n.t('common.unknownError')}`
    })
  } finally {
    loadingServers.value = false;
  }
}

const fetchSettings = async () => {
  try {
    const settingsData = await appStore.getSettings()
    if (settingsData) {
      // Merge with default values to ensure all fields exist
      mergeWithDefaults(settingsData, settings)
    }
  } catch (error) {
    console.error('Error fetching settings:', error)
    showError(i18n.t('settings.errorFetchingSettings'))
  }
}

const fetchTemplates = async () => {
  loadingTemplates.value = true
  try {
    await appStore.fetchTemplates()
    const templates = appStore.templates
    templateOptions.value = templates.map(template => ({
      title: template.name,
      value: template.id
    }))
    
    // Add default template if not in list
    const hasDefault = templateOptions.value.some(t => t.value === 'default')
    if (!hasDefault) {
      templateOptions.value.unshift({
        title: i18n.t('templates.default'),
        value: 'default'
      })
    }
  } catch (error) {
    console.error('Error fetching templates:', error)
  } finally {
    loadingTemplates.value = false
  }
}

const fetchUsers = async () => {
  if (!isAdmin.value) return
  
  loadingUsers.value = true
  try {
    const usersData = await authStore.fetchUsers()
    
    // Handle different response formats
    if (Array.isArray(usersData)) {
      users.value = usersData
    } else if (typeof usersData === 'object' && usersData !== null) {
      // Transform object to array
      users.value = Object.entries(usersData).map(([username, data]) => ({
        username,
        ...data
      }))
    } else {
      console.error("Unexpected response format:", usersData)
      users.value = []
    }
  } catch (error) {
    console.error('Error fetching users:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.errorFetchingUsers')}: ${error.message || i18n.t('common.unknownError')}`
    })
  } finally {
    loadingUsers.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return i18n.t('common.never')
  
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const openUserDialog = (userData) => {
  if (userData) {
    // Edit existing user
    userDialog.isEdit = true
    userDialog.data = {
      username: userData.username,
      display_name: userData.display_name || '',
      password: '', // Keep password empty
      is_admin: userData.is_admin || false,
      auth_type: userData.auth_type || 'internal'
    }
  } else {
    // Create new user
    userDialog.isEdit = false
    userDialog.data = {
      username: '',
      display_name: '',
      password: '',
      is_admin: false,
      auth_type: 'internal'
    }
  }
  
  userDialog.show = true
  showUserPassword.value = false
  
  // Focus and select first input on next tick
  nextTick(() => {
    if (userForm.value) {
      const input = userForm.value.$el.querySelector('input')
      if (input) {
        input.focus()
        input.select()
      }
    }
  })
}

const openServerDialog = (serverData) => {
  if (serverData) {
    // Edit existing server
    serverDialog.isEdit = true;
    serverDialog.data = {
      id: serverData.id,
      name: serverData.name || '',
      url: serverData.url || '',
      username: serverData.username || '',
      password:  serverData.password || '',
      is_default: serverData.is_default || false
    }
  } else {
    // Neuen Server erstellen
    serverDialog.isEdit = false
    serverDialog.data = {
      id: '',
      name: '',
      url: 'http://localhost:3000',
      username: 'admin',
      password: '',
      is_default: servers.value.length === 0 // Erster Server = Default-Server
    }
  }
  
  serverDialog.show = true
  showServerPassword.value = false
  
  // Fokus und Auswahl des ersten Inputs im nächsten Tick
  nextTick(() => {
    if (serverForm.value) {
      const input = serverForm.value.$el.querySelector('input')
      if (input) {
        input.focus()
        input.select()
      }
    }
  })
}

const saveServer = async () => {
  if (serverForm.value && !serverDialog.valid) return;
  
  try {
    if (serverDialog.isEdit) {
      // Bestehenden Server aktualisieren
      const serverId = serverDialog.data.id;
      const serverData = { ...serverDialog.data }
      
      // Leeres Passwort entfernen, um Überschreiben zu vermeiden
      if (!serverData.password) delete serverData.password;
      
      await appStore.updateServer(serverId, serverData)
    } else {
      // Neuen Server erstellen
      await appStore.createServer(serverDialog.data)
    }
    
    // Server-Liste aktualisieren
    await fetchServers()
    
    // Apply everything
    //if (servers.value.length === 1) {
    await applySettings()
    //}
    
    // Erfolgsmeldung anzeigen
    emitter.emit('show-notification', {
      type: 'success',
      text: serverDialog.isEdit 
        ? i18n.t('settings.serverUpdated')
        : i18n.t('settings.serverCreated')
    })
    
    // Dialog schließen
    serverDialog.show = false
  } catch (error) {
    console.error('Error saving server:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.errorSavingServer')}: ${error.response?.data?.detail || error.message || i18n.t('common.unknownError')}`
    })
  }
}

// Methode zum Bestätigen des Löschens eines Servers
const confirmDeleteServer = (serverData) => {
  if (serverData.is_default) {
    emitter.emit('show-notification', {
      type: 'warning',
      text: i18n.t('settings.cannotDeleteDefaultServer')
    })
    return
  }
  
  if (servers.value.length <= 1) {
    emitter.emit('show-notification', {
      type: 'warning',
      text: i18n.t('settings.cannotDeleteLastServer')
    })
    return
  }
  
  emitter.emit('show-confirm-dialog', {
    title: i18n.t('settings.deleteServer'),
    message: i18n.t('settings.deleteServerConfirm', { name: serverData.name }),
    confirmText: i18n.t('common.delete'),
    cancelText: i18n.t('common.cancel'),
    confirmColor: 'error',
    onConfirm: () => deleteServer(serverData.id)
  })
}

// Methode zum Löschen eines Servers
const deleteServer = async (serverId) => {
  try {
    await appStore.deleteServer(serverId);
    
    // Server-Liste aktualisieren
    await fetchServers();
    
    // Erfolgsmeldung anzeigen
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('settings.serverDeleted')
    })
  } catch (error) {
    console.error('Error deleting server:', error);
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.errorDeletingServer')}: ${error.response?.data?.detail || error.message || i18n.t('common.unknownError')}`
    })
  }
}

// Methode zum Setzen eines Servers als Default
const setDefaultServer = async (serverData) => {
  if (serverData.is_default) return
  
  try {
    // Die is_default-Eigenschaft auf true setzen
    const updatedServer = { ...serverData, is_default: true }
    await appStore.updateServer(updatedServer.id, updatedServer)
    
    // Server-Liste aktualisieren
    await fetchServers()
    
    // Erfolgsmeldung anzeigen
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('settings.serverSetAsDefault', { name: serverData.name })
    })
  } catch (error) {
    console.error('Error setting default server:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.errorSettingDefaultServer')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

const saveUser = async () => {
  if (userForm.value && !userDialog.valid) return
  
  userSaving.value = true
  try {
    if (userDialog.isEdit) {
      // Update existing user
      const username = userDialog.data.username
      // Remove empty password to avoid overwriting it
      const userData = {...userDialog.data}
      if (!userData.password) delete userData.password
      
      await authStore.updateUser({ username, userData })
    } else {
      // Create new user
      await authStore.createUser(userDialog.data)
    }
    
    // Reload user list
    await fetchUsers()
    
    // Show success message
    emitter.emit('show-notification', {
      type: 'success',
      text: userDialog.isEdit 
        ? i18n.t('settings.userUpdated')
        : i18n.t('settings.userCreated')
    })
    
    // Close dialog
    userDialog.show = false
  } catch (error) {
    console.error('Error saving user:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.errorSavingUser')}: ${error.response?.data?.detail || error.message || i18n.t('common.unknownError')}`
    })
  } finally {
    userSaving.value = false
  }
}

const confirmDeleteUser = (userData) => {
  if (isLastAdmin(userData) || isCurrentUser(userData)) return
  
  emitter.emit('show-confirm-dialog', {
    title: i18n.t('settings.deleteUser'),
    message: i18n.t('settings.deleteUserConfirm', { name: userData.display_name || userData.username }),
    confirmText: i18n.t('common.delete'),
    cancelText: i18n.t('common.cancel'),
    confirmColor: 'error',
    onConfirm: () => deleteUser(userData.username)
  })
}

const deleteUser = async (username) => {
  try {
    await authStore.deleteUser(username)
    
    // Reload user list
    await fetchUsers()
    
    // Show success message
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('settings.userDeleted')
    })
  } catch (error) {
    console.error('Error deleting user:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.errorDeletingUser')}: ${error.response?.data?.detail || error.message || i18n.t('common.unknownError')}`
    })
  }
}

const isLastAdmin = (userData) => {
  if (!userData.is_admin) return false
  
  // Count how many admins we have
  const adminCount = users.value.filter(u => u.is_admin).length
  return adminCount <= 1
}

const isCurrentUser = (userData) => {
  return user.value && user.value.username === userData.username
}

const saveSettings = async () => {
  if (form.value && !valid.value) return
  
  saving.value = true
  hideAlerts()
  
  try {
    // Hole die aktuellen Einstellungen vom Backend
    const currentSettings = await appStore.getSettings()
    
    // Erstelle eine Kopie der aktuellen Einstellungen
    const updatedSettings = JSON.parse(JSON.stringify(currentSettings))
    
    // Ersetze nur die Kategorien, die in der UI geändert wurden
    Object.keys(settings).forEach(category => {
      if (category === "grafana_servers") {
        // Für Server verwenden wir die aktuelle Liste aus der UI
        updatedSettings[category] = servers.value
      } 
      else if (category === "grafana_selectors") {
        // Für Selektoren auch die aktuelle Liste verwenden
        updatedSettings[category] = settings[category]
      }
      else if (typeof settings[category] === 'object') {
        if (!(category in updatedSettings)) {
          updatedSettings[category] = {}
        }
        updatedSettings[category] = {...updatedSettings[category], ...settings[category]}
      } else {
        updatedSettings[category] = settings[category]
      }
    });
    
    // Speichere die aktualisierten Einstellungen
    await appStore.updateSettings(updatedSettings)

    // Automatically apply settings
    try {
      await appStore.applySettings()
      
      // Add a small delay to let the backend apply changes
      setTimeout(() => {
        // Reload data in ReportDesigner
        appStore.fetchOrganizations()
      }, 500)
      
      // Emit settings-updated event
      emitter.emit('settings-updated')

      // Show success notification
      emitter.emit('show-notification', {
        type: 'success',
        text: i18n.t('settings.settingsAppliedAutomatically')
      })
    } catch (applyError) {
      // Show warning if settings were saved but not applied
      emitter.emit('show-notification', {
        type: 'warning',
        text: i18n.t('settings.savedButNotApplied')
      })
    }
    
    showSuccess()
  } catch (error) {
    showError(error.message || i18n.t('settings.errorSavingSettings'))
  } finally {
    saving.value = false
  }
}

const testAllServerConnections = async () => {
  for (const server of servers.value) {
    try {
      const result = await appStore.testServerConnection(server.id, {
        name: server.name,
        url: server.url,
        username: server.username,
        password: server.password
      })
      
      // Update server status based on test result
      server.status = result.success ? 'connected' : 'error'
      server.lastTested = new Date().toISOString()
    } catch (error) {
      console.error(`Error testing server ${server.id}: ${error}`)
      server.status = 'error'
    }
  }
}

const testServerConnection = async (serverData) => {
  serverTestResult.value = null
  
  try {
    // Kopie der Serverdaten erstellen für den Test
    const testData = {
      name: serverData.name,
      url: serverData.url,
      username: serverData.username,
      password: serverData.password
    }
    
    // Server-Verbindung testen
    serverTestResult.value = await appStore.testServerConnection(
      serverData.id,
      testData
    )
    
    // Ergebnis anzeigen
    emitter.emit('show-notification', {
      type: serverTestResult.value.success ? 'success' : 'error',
      text: serverTestResult.value.message
    })
  } catch (error) {
    console.error('Error testing server connection:', error);
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.testConnectionError')}: ${error.message || i18n.t('common.unknownError')}`
    })
  }
}

const testEmailSettings = async () => {
  testingEmail.value = true
  emailTestResult.value = null
  
  try {
    const result = await appStore.testEmailSettings({
      server: settings.email.server,
      port: settings.email.port,
      username: settings.email.username,
      password: settings.email.password,
      sender: settings.email.sender,
      useTLS: settings.email.useTLS
    })
    
    emailTestResult.value = {
      success: result.success,
      message: result.success 
        ? i18n.t('settings.emailTestSuccess') 
        : `${i18n.t('settings.emailTestError')}: ${result.message || i18n.t('common.unknownError')}`
    }
  } catch (error) {
    console.error('Error testing email settings:', error)
    emailTestResult.value = {
      success: false,
      message: `${i18n.t('settings.emailTestError')}: ${error.message || i18n.t('common.unknownError')}`
    }
  } finally {
    testingEmail.value = false
  }
}

const testLdapConnection = async () => {
  testingLdap.value = true
  ldapTestResult.value = null
  
  try {
    const result = await appStore.testLdapConnection(settings.ldap)
    
    ldapTestResult.value = {
      success: result.success,
      message: result.success 
        ? i18n.t('settings.ldapConnectionSuccess') 
        : `${i18n.t('settings.ldapConnectionError')}: ${result.message || i18n.t('common.unknownError')}`
    }
  } catch (error) {
    console.error('Error testing LDAP connection:', error)
    ldapTestResult.value = {
      success: false,
      message: `${i18n.t('settings.ldapConnectionError')}: ${error.message || i18n.t('common.unknownError')}`
    }
  } finally {
    testingLdap.value = false
  }
}

const applySettings = async () => {
  applying.value = true
  
  try {
    await appStore.applySettings()
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('settings.settingsApplied')
    })
  } catch (error) {
    console.error('Error applying settings:', error)
    emitter.emit('show-notification', {
      type: 'error',
      text: `${i18n.t('settings.errorApplyingSettings')}: ${error.message || i18n.t('common.unknownError')}`
    })
  } finally {
    applying.value = false
  }
}

const checkIfFirstStart = async () => {
  try {
    const result = await appStore.checkSettingsInitialized()
    isFirstStart.value = !result.initialized
    
    // Switch to Grafana tab on first start
    if (isFirstStart.value) {
      activeTab.value = 'grafana'
      
      emitter.emit('show-notification', {
        type: 'info',
        text: i18n.t('settings.welcomeMessage'),
        timeout: 10000
      })
    }
  } catch (error) {
    console.error('Error checking if first start:', error)
  }
}

const mergeWithDefaults = (sourceSettings, targetSettings) => {
  for (const category in sourceSettings) {
    if (category in targetSettings) {
      Object.assign(targetSettings[category], sourceSettings[category])
    } else {
      targetSettings[category] = sourceSettings[category]
    }
  }
}

const showSuccess = () => {
  showSuccessAlert.value = true
  // Auto-hide after 5 seconds
  setTimeout(() => {
    showSuccessAlert.value = false
  }, 5000)
}

const showError = (message) => {
  errorMessage.value = message
  showErrorAlert.value = true
}

const hideAlerts = () => {
  showSuccessAlert.value = false
  showErrorAlert.value = false
  errorMessage.value = ''
}

const selectorHeaders = ref([])
const loadingSelectors = ref(false)

// Methode zum Aktualisieren der Selector-Header
const updateSelectorHeaders = () => {
  selectorHeaders.value = [
    { title: i18n.t('settings.selectorVersion'), key: 'version' },
    { title: i18n.t('settings.selectorValue'), key: 'selector' },
    { title: i18n.t('common.actions'), key: 'actions', sortable: false }
  ]
}

// Selektor-Dialog-Zustand
const selectorDialog = reactive({
  show: false,
  isEdit: false,
  valid: true,
  editIndex: -1,
  data: {
    version: '',
    selector: ''
  }
})

// Methode zum Hinzufügen eines neuen Selektors
const addSelector = () => {
  selectorDialog.isEdit = false;
  selectorDialog.editIndex = -1;
  selectorDialog.data = {
    version: '',
    selector: ''
  }
  selectorDialog.show = true;
}

// Methode zum Bearbeiten eines bestehenden Selektors
const editSelector = (item) => {
  const index = settings.grafana_selectors.findIndex(
    s => s.version === item.version && s.selector === item.selector
  )
  
  if (index >= 0) {
    selectorDialog.isEdit = true
    selectorDialog.editIndex = index
    selectorDialog.data = { ...settings.grafana_selectors[index] }
    selectorDialog.show = true
  }
}

// Methode zum Bestätigen des Löschens eines Selektors
const confirmDeleteSelector = (item) => {
  emitter.emit('show-confirm-dialog', {
    title: i18n.t('settings.deleteSelector'),
    message: i18n.t('settings.deleteSelectorConfirm', { version: item.version }),
    confirmText: i18n.t('common.delete'),
    cancelText: i18n.t('common.cancel'),
    confirmColor: 'error',
    onConfirm: () => deleteSelector(item)
  })
}

// Methode zum Löschen eines Selektors
const deleteSelector = (item) => {
  const index = settings.grafana_selectors.findIndex(
    s => s.version === item.version && s.selector === item.selector
  )
  
  if (index >= 0) {
    settings.grafana_selectors.splice(index, 1);
    
    // Erfolgsmeldung anzeigen
    emitter.emit('show-notification', {
      type: 'success',
      text: i18n.t('settings.selectorDeleted')
    })
  }
}

// Methode zum Speichern eines Selektors
const saveSelector = () => {
  if (!selectorDialog.valid) return
  
  // Sicherstellen, dass das Array existiert
  if (!settings.grafana_selectors) {
    settings.grafana_selectors = []
  }
  
  if (selectorDialog.isEdit && selectorDialog.editIndex >= 0) {
    // Selektor aktualisieren
    settings.grafana_selectors[selectorDialog.editIndex] = { ...selectorDialog.data }
  } else {
    // Neuen Selektor hinzufügen
    settings.grafana_selectors.push({ ...selectorDialog.data })
  }
  
  // Dialog schließen
  selectorDialog.show = false
  
  // Erfolgsmeldung anzeigen
  emitter.emit('show-notification', {
    type: 'success',
    text: selectorDialog.isEdit ? 
      i18n.t('settings.selectorUpdated') : 
      i18n.t('settings.selectorCreated')
  })
}

let intervalId
// Lifecycle hooks
onMounted(async () => {
  fetchSettings()
  fetchTemplates()
  fetchServers()
  checkIfFirstStart()
  updateSelectorHeaders()
  updateUserHeaders()
  updateServerHeaders()
  
  if (isAdmin.value) {
    fetchUsers()
  }
  
  await testAllServerConnections()
  intervalId = setInterval(async() => {
    await testAllServerConnections()
  }, 2000)
  
  // If user is not admin, show general tab
  if (!isAdmin.value) {
    activeTab.value = 'general'
  }
  
  // Listen for language changes
  emitter.on('language-changed', () => {
    updateSelectorHeaders()
    updateServerHeaders()
    updateUserHeaders()
  })

})

// Watch for locale changes
watch(() => i18n.locale.value, () => {
  updateSelectorHeaders()
  updateServerHeaders()
  updateUserHeaders()
})

onBeforeUnmount(() => {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
})
</script>

<style scoped>
.settings-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>

