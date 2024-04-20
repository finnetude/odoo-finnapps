/** @odoo-module **/

// Import des modules et fonctions nécessaires :
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useEffect, useRef, useState, onWillStart } from "@odoo/owl";

export class finn_solde_compte extends Component {

    // Template utilisé par le composant :
    static template = "finnapps_solde_compte.clientaction";

    setup() {

        // Initialisation des variables d'état du composant
        this.state = useState({
            lines: [],
            length: 0,
            expandedGroups: new Set(),
            journals: [],
            exercises: [],
            periods: [],
            selectedJournal: null,
            selectedExercise: null,
            selectedPeriod: null,
        });
        this.state.topLevelTotals = {
            totalDebit: 0,
            totalCredit: 0,
            totalBalance: 0
        };

        this.action = useService("action");
        this.orm = useService("orm");

        // Fonction exécutée avant le démarrage
        onWillStart(async () => {
            await this.loadAccountData();
            await this.loadJournals();
            await this.loadExercises();
            await this.loadPeriods();
        });

        // Liaison des méthodes de gestion des filtres
        this.toggleGroup = this.toggleGroup.bind(this);
        this.handleJournalFilterChange = this.handleJournalFilterChange.bind(this);
        this.handleExerciseFilterChange = this.handleExerciseFilterChange.bind(this);
        this.handlePeriodFilterChange = this.handlePeriodFilterChange.bind(this);


    }

    // ***** Chargement des données **************************************************************************

    // Chargement des données des comptes :
    async loadAccountData() {
        try {

            // Initialisation des totaux : 
            const topLevelTotals = {
                totalDebit: 0,
                totalCredit: 0,
                totalBalance: 0
            };

            // Définition du domaine de recherche en fonction des filtres sélectionnés : 
            const domain = [];
            if (this.state.selectedJournal) {
                console.log(this.state.selectedJournal)
                domain.push(['journal_id', '=', this.state.selectedJournal]);
            } if (this.state.selectedExercise) {
                console.log(this.state.selectedExercise)

                domain.push(['period_id.exercice_id', '=', this.state.selectedExercise]);
            } if (this.state.selectedPeriod) {
                console.log(this.state.selectedPeriod)

                domain.push(['period_id', '=', this.state.selectedPeriod]);
            }

            // Récupération des comptes : 
            const accounts = await this.orm.call("account.account", "search_read", [], {
                fields: ["id", "code", "name", "group_id"],
            });
            // Récupération des identifiants de groupe : 
            const groupIds = accounts.map(account => account.group_id[0]);

            // Récupération des groupes : 
            const accounts_groups = await this.orm.call("account.group", "search_read", [[]],
                {
                    fields: ["name", "code_prefix_start", "parent_id", "code_prefix_start"],
                });
            const groups = await this.orm.call("account.group", "read", [groupIds],
                {
                    fields: ["id", "name", "parent_id", "code_prefix_start"],
                });
            const accountsGroups = await this.orm.call("account.group", "search_read", [[]],
                {
                    fields: ["name", "code_prefix_start", "parent_id", "code_prefix_start"],
                });

            // Récupération des lignes de mouvement comptable :
            const moveLines = await this.orm.call("account.move.line", "search_read", [domain],
                {
                    fields: ["debit", "credit", "balance", "journal_id", "account_id"],
                });

            // Regroupement des lignes de mouvement par compte :
            const moveLinesByAccount = {};
            moveLines.forEach(moveLine => {
                const accountId = moveLine.account_id[0];
                if (!moveLinesByAccount[accountId]) {
                    moveLinesByAccount[accountId] = [];
                }
                moveLinesByAccount[accountId].push(moveLine);
            });

            // Calcul des totaux pour chaque compte : 
            accounts.forEach(account => {
                const accountId = account.id;
                const mvlines = moveLinesByAccount[accountId] || [];
                const debit = mvlines.reduce((total, line) => total + (line.debit || 0), 0);
                const credit = mvlines.reduce((total, line) => total + (line.credit || 0), 0);
                account.debit = parseFloat(debit.toFixed(2));
                account.credit = parseFloat(credit.toFixed(2));
                const balance = debit - credit;
                account.balance = parseFloat(balance.toFixed(2));
            });

            // Regrouper les comptes par groupe :
            const AccountByGroup = {};
            accounts.forEach(accounts => {
                const groupId = accounts.group_id[0];
                if (!AccountByGroup[groupId]) {
                    AccountByGroup[groupId] = [];
                }
                AccountByGroup[groupId].push(accounts);
            });

            // Regrouper les groupes par groupe parent :
            const groupsByGroup = {};
            accounts_groups.forEach(group_child => {
                const groupId = group_child.parent_id[0];
                if (!groupsByGroup[groupId]) {
                    groupsByGroup[groupId] = [];
                }
                groupsByGroup[groupId].push(group_child);
            });

            // Calcul des totaux pour chaque groupe : 
            accounts_groups.forEach(group => {
                const groupId = group.id;
                const accountlines = AccountByGroup[groupId] || [];
                const accountlines2 = groupsByGroup[groupId] || [];
                const debit = accountlines.reduce((total, line) => total + (line.debit || 0), 0);
                const credit = accountlines.reduce((total, line) => total + (line.credit || 0), 0);
                const debit2 = accountlines2.reduce((total, line) => total + (line.debit || 0), 0);
                const credit2 = accountlines2.reduce((total, line) => total + (line.credit || 0), 0);
                const group_debit = debit + debit2;
                group.debit = parseFloat(group_debit.toFixed(2));

                const group_credit = credit + credit2;
                group.credit = parseFloat(group_credit.toFixed(2));

                const group_balance = group.debit - group.credit;
                group.balance = parseFloat(group_balance.toFixed(2));
            });

            // Mapping des groupes par identifiant : 
            const groupsMap = {};
            accounts_groups.forEach(group => {
                groupsMap[group.id] = group.id;
            });

            // Récupération des groupes enfants pour chaque groupe : 
            const fetchChildGroups = (groupId) => {
                const children = accounts_groups.filter(group => group.parent_id[0] === groupId);
                return children.flatMap(child => [child, ...fetchChildGroups(child.id)]);
            };
            accounts_groups.forEach(group => {
                groupsMap[group.id] = group.id;
                const children = fetchChildGroups(group.id);
                children.forEach(child => groupsMap[child.id] = group.id);
            });
            accounts.forEach(account => {
                account.groupId = groupsMap[account.group_id[0]];
            });

            // Récupération des groupes de niveau supérieur:
            const topLevelGroups = accounts_groups.filter(group => !group.parent_id);

            // Calcul des totaux de niveau supérieur :
            topLevelGroups.forEach(group => {
                const groupId = group.id;
                const accountlines = AccountByGroup[groupId] || [];
                const accountlines2 = groupsByGroup[groupId] || [];
                const debit = accountlines.reduce((total, line) => total + (line.debit || 0), 0);
                const credit = accountlines.reduce((total, line) => total + (line.credit || 0), 0);
                const debit2 = accountlines2.reduce((total, line) => total + (line.debit || 0), 0);
                const credit2 = accountlines2.reduce((total, line) => total + (line.credit || 0), 0);

                const group_debit = debit + debit2;
                group.debit = parseFloat(group_debit.toFixed(2));

                const group_credit = credit + credit2;
                group.credit = parseFloat(group_credit.toFixed(2));

                const group_balance = group.debit - group.credit;
                group.balance = parseFloat(group_balance.toFixed(2));


            });

            topLevelGroups.forEach(group => {
                topLevelTotals.totalDebit += group.debit || 0;
                topLevelTotals.totalCredit += group.credit || 0;
                topLevelTotals.totalBalance += group.balance || 0;
            });

            this.state.topLevelTotals = topLevelTotals;
            this.state.topLevelGroups = topLevelGroups;
            this.state.lines = accounts;
            this.state.grp = accounts_groups;
            this.state.groups = accounts_groups;
            this.state.length = this.state.lines.length;

        } catch (error) {
        }
    }

    // Chargement des journaux :
    async loadJournals() {
        try {
            const journals = await this.orm.call("account.journal", "search_read", [[]], {
                fields: ["name", "id"]
            });
            this.state.journals = journals;
        } catch (error) {
        }
    }

    // Chargement des exercices :
    async loadExercises() {
        try {
            const Exercises = await this.orm.call("finn.exercice", "search_read", [[]], {
                fields: ["name", "id"]
            });
            this.state.exercises = Exercises;
        } catch (error) {
        }
    }

    // Chargement des périodes :
    async loadPeriods() {
        try {
            const Periods = await this.orm.call("finn.periode", "search_read", [[]], {
                fields: ["name", "id"]
            });
            this.state.periods = Periods;
        } catch (error) {
        }
    }


    // ***** Gestion du changement de filtrage ***************************************************************

    // Gestion du changement de filtre pour le journal :
    async handleJournalFilterChange(value) {
        const selectedValue = value;
        this.state.selectedJournal = selectedValue;
        await this.loadAccountData();

    }

    // Gestion du changement de filtre pour l'exercice :
    async handleExerciseFilterChange(value) {
        const selectedValue = value;

        this.state.selectedExercise = selectedValue;
        await this.loadAccountData();

    }

    // Gestion du changement de filtre pour la période :
    async handlePeriodFilterChange(value) {
        const selectedValue = value;
        this.state.selectedPeriod = selectedValue;
        await this.loadAccountData();

    }


    // ***** Méthodes pour gérer l'affichage des groupes *****************************************************

    // Récupérer les groups-childs :
    getChildGroups(parentGroupId) {
        const childGroups = this.state.groups.filter(group => group.parent_id && group.parent_id[0] === parentGroupId);
        const uniqueChildGroups = Array.from(new Set(childGroups.map(group => JSON.stringify(group))))
            .map(groupString => JSON.parse(groupString));

        return uniqueChildGroups;
    }

    // Gérer les balise fermant/ouvrante :

    isGroupExpanded(groupId) {

        return this.state.expandedGroups.has(groupId);
    }

    toggleGroup(groupId) {

        const expandedGroups = new Set(this.state.expandedGroups);

        if (expandedGroups.has(groupId)) {
            expandedGroups.delete(groupId);
        } else {
            expandedGroups.add(groupId);
        }

        this.state.expandedGroups = expandedGroups;
    }

    expandChildGroups(groupId, expandedGroups, processedGroups) {
        if (processedGroups.has(groupId)) {
            return;
        }

        processedGroups.add(groupId);

        const childGroups = this.getChildGroups(groupId);
        childGroups.forEach(childGroupId => {
            if (!expandedGroups.has(childGroupId)) {
                expandedGroups.add(childGroupId);
                this.expandChildGroups(childGroupId, expandedGroups, processedGroups);
            }
        });
    }


    // ***** Méthodes pour rediriger vers un groupe ou un compte spécifique *****************************************************

    // Vers un groupe : 
    redirectToGroup = async (groupId) => {
        try {
            const group = this.state.grp.find(group => group.id === groupId);
            if (group) {
                await this.action.doAction({
                    type: 'ir.actions.act_window',
                    res_model: 'account.group',
                    res_id: group.id,
                    views: [[false, 'form']],
                    target: 'current'
                });
            }
        } catch (error) {

        }
    }

    // Vers un compte spécifique : 
    redirectToAccount = async (accountId) => {
        try {
            const account = this.state.lines.find(account => account.id === accountId);
            if (account) {
                await this.action.doAction({
                    type: 'ir.actions.act_window',
                    res_model: 'account.account',
                    res_id: account.id,
                    views: [[false, 'form']],
                    target: 'current'
                });
            }
        } catch (error) {

        }
    }

}

// Définition du template :
finn_solde_compte.template = "finnapps_solde_compte.clientaction";

// Enregistrement de la classe dans le registre des actions :
registry.category("actions").add("finnapps_solde_compte.finn_solde_compte", finn_solde_compte);