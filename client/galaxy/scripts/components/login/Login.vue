<template>
    <div class="container">
        <div class="row justify-content-md-center">
            <div class="col col-lg-6">
                <b-alert :show="messageShow" :variant="messageVariant" v-html="messageText" />
                <b-form id="login" @submit.prevent="submitGalaxyLogin()">
                    <b-card no-body header="Welcome to Galaxy, please log in">
                        <b-card-body>
                            <b-form-group label="Public name or Email Address">
                                <b-form-input name="login" type="text" v-model="login" />
                            </b-form-group>
                            <b-form-group label="Password">
                                <b-form-input name="password" type="password" v-model="password" />
                                <b-form-text
                                    >Forgot password?
                                    <a @click="reset" href="javascript:void(0)" role="button"
                                        >Click here to reset your password.</a
                                    >
                                </b-form-text>
                            </b-form-group>
                            <b-button name="login" type="submit">Login</b-button>
                        </b-card-body>
                        <b-card-footer>
                            Don't have an account?
                            <span v-if="allowUserCreation">
                                <a
                                    id="register-toggle"
                                    href="javascript:void(0)"
                                    role="button"
                                    @click.prevent="toggleLogin"
                                    >Register here.</a
                                >
                            </span>
                            <span v-else>
                                Registration for this Galaxy instance is disabled. Please contact an administrator for
                                assistance.
                            </span>
                        </b-card-footer>
                    </b-card>
                </b-form>
            </div>

            <div class="col col-lg-6">
                <div class="cilogon" v-if="cilogonShow">
                    <!--Only Display if CILogon is configured-->
                    <div class="cilogon-prompt">
                        <h2>Use your existing institutional login</h2>
                        <span class="hint">e.g., university, lab, facility, project</span>
                    </div>
                    
                    <selectize v-model="selected" placeholder="Select your institution:">
                        <option v-for="idp in cilogon_idps" :key="idp.EntityID" :value="idp.EntityID">
                            {{ idp.DisplayName }}
                        </option>
                    </selectize>

                    <b-button class="d-block mt-3" @click="submitCILogon()">
                        <i v-bind:class="oidc_idps_icons[idp]"/> Sign in with Institutional Credentials*
                    </b-button>

                    <p>*Galaxy uses CILogon to enable you to Log In from this organization. 
                        By clicking 'Sign In', you agree to the <a href="https://ca.cilogon.org/policy/privacy">
                        CILogon privacy policy</a> and you agree to share your username, email address, and 
                        affiliation with CILogon and Galaxy. You also agree for CILogon to issue a certificate 
                        that allows Galaxy to act on your behalf.
                    </p>
                </div>

                <!--<div v-for="idp in oidc_idps" :key="idp" style="margin:0.5em">
                    <span v-if="oidc_idps_icons[idp]">
                        <img v-bind:src="oidc_idps_icons[idp]" height="45" v-bind:alt="idp" />
                    </span>
                    <span v-else>
                        <b-button class="d-block mt-3" @click="submitOIDCLogin(idp)">
                            <i v-bind:class="oidc_idps_icons[idp]" /> Sign in with
                            {{ idp.charAt(0).toUpperCase() + idp.slice(1) }}
                        </b-button>
                    </span>
                </div>-->

                <div>
                    <b-button v-for="idp in filtered_oidc_idps" :key="idp" class="d-block mt-3" @click="submitOIDCLogin(idp)">
                        <i v-bind:class="oidc_idps_icons[idp]" /> Sign in with
                        {{ idp.charAt(0).toUpperCase() + idp.slice(1) }}
                    </b-button>
                </div>
            </div>

            <div>
                <template v-if="showLinkAccount">
                    <linkAccounts :show_welcome_with_login="show_welcome_with_login" :welcome_url="welcome_url" />
                </template>
            </div>
            <div v-if="show_welcome_with_login" class="col">
                <b-embed type="iframe" :src="welcome_url" aspect="1by1" />
            </div>
        </div>
    </div>
</template>

<script>
import axios from "axios";
import Vue from "vue";
import Selectize from 'vue2-selectize';
import LinkAccounts from "components/login/LinkAccounts.vue";
import BootstrapVue from "bootstrap-vue";
import { getGalaxyInstance } from "app";
import { getAppRoot } from "onload";

Vue.use(BootstrapVue);

export default {
    components: {
        Selectize,
        linkAccounts: LinkAccounts
    },
    props: {
        show_welcome_with_login: {
            type: Boolean,
            required: false
        },
        welcome_url: {
            type: String,
            required: false
        }
    },
    data() {
        const galaxy = getGalaxyInstance();
        const oidc_idps = galaxy.config.oidc;
        // Icons to use for each IdP
        const oidc_idps_icons = {
            google: "https://developers.google.com/identity/images/btn_google_signin_light_normal_web.png",
            elixir: "https://elixir-europe.org/sites/default/files/images/login-button-orange.png"
        };
        // Add default icons to IdPs without icons
        oidc_idps
            .filter(function(key) {
                return oidc_idps_icons[key] === undefined;
            })
            .forEach(function(idp) {
                oidc_idps_icons[idp] = "fa fa-id-card";
            });
        return {
            login: null,
            password: null,
            url: null,
            provider: null,
            messageText: null,
            messageVariant: null,
            allowUserCreation: galaxy.config.allow_user_creation,
            redirect: galaxy.params.redirect,
            session_csrf_token: galaxy.session_csrf_token,
            enable_oidc: galaxy.config.enable_oidc,
            oidc_idps: oidc_idps,
            oidc_idps_icons: oidc_idps_icons,
            cilogon_idps: [],
            selected: '',
            linkPrompt: false
        };
    },
    computed: {
        filtered_oidc_idps() {
            return this.oidc_idps.filter(idp => idp != "cilogon");
        },
        cilogonShow() {
            return this.oidc_idps.includes("cilogon");
        },
        messageShow() {
            return this.messageText != null;
        },
        showLinkAccount() {
            return this.linkPrompt;
        }
    },
    methods: {
        toggleLogin: function() {
            if (this.$root.toggleLogin) {
                this.$root.toggleLogin();
            }
        },
        submitGalaxyLogin: function(method) {
            const rootUrl = getAppRoot();
            axios
                .post(`${rootUrl}user/login`, this.$data)
                .then(response => {
                    if (response.data.message && response.data.status) {
                        alert(response.data.message);
                    }
                    if (response.data.expired_user) {
                        window.location = `${rootUrl}root/login?expired_user=${response.data.expired_user}`;
                    } else if (response.data.redirect) {
                        window.location = encodeURI(response.data.redirect);
                    } else {
                        window.location = `${rootUrl}`;
                    }
                })
                .catch(error => {
                    this.messageVariant = "danger";
                    const message = error.response.data && error.response.data.err_msg;
                    this.messageText = message || "Login failed for an unknown reason.";
                });
        },
        submitOIDCLogin: function(idp) {
            const rootUrl = getAppRoot();
            axios
                .post(`${rootUrl}authnz/${idp}/login`)
                .then(response => {
                    if (response.data.redirect_uri) {
                        window.location = response.data.redirect_uri;
                    }
                    // Else do something intelligent or maybe throw an error -- what else does this endpoint possibly return?
                })
                .catch(error => {
                    this.messageVariant = "danger";
                    const message = error.response.data && error.response.data.err_msg;
                    this.messageText = message || "Login failed for an unknown reason.";
                });
        },
        reset: function(ev) {
            const rootUrl = getAppRoot();
            ev.preventDefault();
            axios
                .post(`${rootUrl}user/reset_password`, { email: this.login })
                .then(response => {
                    this.messageVariant = "info";
                    this.messageText = response.data.message;
                })
                .catch(error => {
                    this.messageVariant = "danger";
                    const message = error.response.data && error.response.data.err_msg;
                    this.messageText = message || "Password reset failed for an unknown reason.";
                });
        },
        getCILogonIdps: function() {
            axios.get('https://cilogon.org/idplist/')
                .then(response => {
                    this.cilogon_idps = response.data;
                    //List is originally sorted by OrganizationName which can be different from DisplayName
                    this.cilogon_idps.sort((a, b) => (a.DisplayName > b.DisplayName) ? 1 : -1);
                });
        },
        submitCILogon: function() {
            const rootUrl = getAppRoot();
            axios
                .post(`${rootUrl}authnz/cilogon/login/?idphint=${this.selected}`)
                .then(response => {
                    console.log(response);
                    console.log(response.data);
                    /*if (response.data.message && response.data.status) {
                        alert(response.data.message);
                    }*/
                    if (response.data.redirect_uri) {
                        window.location = response.data.redirect_uri;
                    }
                    /*
                        if user first time logging in, prompt and ask if want to connect to existing Galaxy account
                        "Reminder: Registration and usage of multiple accounts is tracked and such accounts are subject to termination and data deletion."
                    */

                    console.log(response.data.status);
                    if (response.data.status == 200 /*and user account created/user first time logging in*/) {
                       this.linkPrompt = true;
                       const Galaxy = getGalaxyInstance();
                       Galaxy.router.push("/LinkAccounts.vue");
                    }
                })
                .catch(error => {
                    this.messageVariant = "danger";
                    const message = error.response.data && error.response.data.err_msg;
                    this.messageText = message || "Login failed for an unknown reason.";
                });
        }
    },
    created() {
        this.getCILogonIdps();
    }
};
</script>

<style lang="scss">
@import "~selectize/dist/css/selectize.bootstrap3.css";
</style>