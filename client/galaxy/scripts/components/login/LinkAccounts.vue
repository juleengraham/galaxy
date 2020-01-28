<template>
    <div class="container">
        <div class="row justify-content-md-center">
            <div id="linkPrompt" v-if="promptOrResult">
                <h1>Link an existing account</h1>

                <p>Do you have an existing Galaxy account that you would like to be linked?</p>
                <p>Reminder: Registration and usage of multiple accounts is tracked and such accounts are subject to termination and data deletion.</p>

                <div class="btn-group" role="group">
                    <b-button class="d-block mt-3" value="yes" @click="showLogin()">Yes</b-button>
                    <b-button class="d-block mt-3" value="no" @click="loadHome()">No</b-button>
                </div>
            </div>

            <div class="col col-lg-6" v-if="!promptOrResult">
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
                    </b-card>
                </b-form>
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
import Selectize from 'vue2-selectize'
import BootstrapVue from "bootstrap-vue";
import { getGalaxyInstance } from "app";
import { getAppRoot } from "onload";

Vue.use(BootstrapVue);

export default {
    components: {
        Selectize
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
            promptOrResult = true
        };
    },
    computed: {
        /*linkPromptShow() {
            return promptOrResult;
        },*/
        messageShow() {
            return this.messageText != null;
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

