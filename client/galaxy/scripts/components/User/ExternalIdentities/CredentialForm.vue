<template>
    <b-form :validated="credential.isValid">

    </b-form>
</template>

<script>
import { Credential, ResourceProviders } from "./model";
import { getIdentityProviders } from "./model/service";
import CredentialConfig from "./CredentialConfig";

export default {
    components: {
        CredentialConfig
    },
    props: {
        value: { type: Credential, required: true }
    },
    data() {
        return {
            identityProviders: []
        };
    },
    computed: {
        credential() {
            return this.value;
        },
        // transformed for bootstrap component
        resourceProviderOptions() {
            return Array.from(ResourceProviders.entries()).map(([value, o]) => ({ value, text: o.label }));
        },
        config() {
            return this.credential.config;
        },
        loading() {
            return this.credential.loading;
        },
        saveButtonDisabled() {
            return !(this.credential.valid && this.credential.dirty);
        },
        saveButtonVariant() {
            return this.saveButtonDisabled ? "secondary" : "primary";
        },
        saveButtonTitle() {
            return this.loading ? "Saving Key..." : "Save Key";
        }
    },
    created() {
        getIdentityProviders().then(result => {
            if (!this.credential.authn_id && result.length == 1) {
                this.credential.authn_id = result[0].authn_id;
                this.credential.updateState();
            }
            this.identityProviders = result;
        });
    }
};
</script>
