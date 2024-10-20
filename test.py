import panel as pn
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from dataclasses import dataclass

pn.extension('floatpanel')  

class App():
    def __init__(self):
        self.medications = pd.DataFrame()

        self.import_data()
        self.medication_overview_panel = pn.panel(MedicationOverview(self, self.medications, self.administers)).servable()
    def import_data(self):
        #medications
        medications_dict = []
        medications_dict.append({
            'name':'olanzapine',
            'start_quantity':30,
            'current_quantity':14,
            'expiration':datetime.date(year=2024, month=11, day=3)})
        medications_dict.append({
            'name':'sertraline',
            'start_quantity':40,
            'current_quantity':19,
            'expiration':datetime.date(year=2024, month=12, day=13)})
        self.medications = pd.DataFrame(medications_dict)
        #self.medications = self.medications.set_index('name')
        #administers
        administers_dict = []
        administers_dict.append({
            'name':'sertraline',
            'repeat':'sunday', #daily, sunday, monday, tuesday, thursday, friday, saturday
            'time':'morning' #morning, mid-day, night, any
        })
        administers_dict.append({
            'name':'sertraline',
            'repeat':'tuesday', #daily, sunday, monday, tuesday, thursday, friday, saturday
            'time':'morning' #morning, mid-day, night, any
        })
        administers_dict.append({
            'name':'olanzapine',
            'repeat':'daily', #daily, sunday, monday, tuesday, thursday, friday, saturday
            'time':'night' #morning, mid-day, night, any
        })
        self.administers = pd.DataFrame(administers_dict)

### Panels ###
class MedicationOverview(pn.GridBox):
    def __init__(self, parent, medications, administers):
        super().__init__(ncols = 2)
        self.append(pn.Card(self.medication_supply(medications, administers), title = 'Current Supply'))
        self.append(pn.Card(self.administer_reminders(medications, administers), title = 'Today\'s Medications'))
        self.append(pn.Card(self.medications_table(parent, medications, administers), title = 'Medications'))
    def medications_table(self, parent, medications, administers):
        container = pn.Column()
        table_list= []
        #print(medications)
        for index, medication in medications.iterrows():
            #print(medication)
            #print(administers)
            medication_administers = []
            for index, administer in administers.iterrows():
                if administer['name'] == medication['name']:
                    medication_administers.append((administer['repeat'], administer['time']))
            table_list.append({
                'Medication':medication['name'],
                'Quantity':f'{medication["current_quantity"]}/{medication["start_quantity"]}',
                'Taken':', '.join(f'{medication_administer[0]} ({medication_administer[1]})' for medication_administer in medication_administers),
                'Expires':medication['expiration']
                })
        #bottom buttons
        container.append(pn.pane.DataFrame(pd.DataFrame(table_list)))
        bottom_row = pn.Row()
        container.append(bottom_row)
        medications_dataframe = pn.widgets.DataFrame(parent.medications)
        bottom_tabs = pn.Tabs(('Edit medications', medications_dataframe), ('Add medication', pn.Row(pn.panel("Medication name:"))), ('Delete medication', print()), dynamic = True)
        container.append(bottom_tabs)
        return container
        return container
    def medication_supply(self, medications, administers):
        #calculate days worth of medications
        daysof_medications = pd.DataFrame({'name' : medications['name'], 'days' : 0})
        daysof_medications = daysof_medications.set_index('name')
        nondaily_medication_administers = []
        #print()
        #print(administers)
        today = datetime.datetime.today()
        for i, administer in administers.iterrows():
            name = administer['name']
            #print(name)
            current_quantity = medications.loc[medications['name'] == name, 'current_quantity'].values[0]
            if administer['repeat'] == 'daily':
                daysof_medications.loc[name, 'days'] += current_quantity
            else:
                if administer['name'] in (x.get('name') for x in nondaily_medication_administers): #add day to existing administer if exists
                    for j, medication in enumerate(nondaily_medication_administers):
                        if medication['name'] == administer['name']:
                            nondaily_medication_administers[j]['days'].append(administer['repeat'])
                else:
                    nondaily_medication_administers.append({'name':administer['name'], 'days':[administer['repeat'],]})
        for medication in nondaily_medication_administers:
            pills_left = current_quantity
            current_date = today
            delta = datetime.timedelta(days = 1)
            for i in range(0, 1000):
                for administer in medication['days']:
                    if current_date.weekday() == ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday').index(administer):
                        pills_left -= 1
                    current_date += delta
                if pills_left < 1:
                    break
            days_between = current_date - today
            daysof_medications.loc[medication['name'], 'days'] = days_between.days
        #plot
        fig = plt.figure(figsize=(6, 4))
        bars = plt.barh(medications['name'], daysof_medications['days'], color='skyblue')
        plt.title('Medication Supply')
        plt.grid(axis='x')
        for i, bar in enumerate(bars):
            plt.annotate(f'{bar.get_width()} days', (bar.get_width(), bar.get_y() + bar.get_height()/2))
            if plt.xlim()[1] < bar.get_width() + 20: #make sure text fits
                plt.xlim(0, bar.get_width() + 20) 
        plt.tight_layout()
        return pn.pane.Matplotlib(fig, tight = True, format="svg", sizing_mode="stretch_width")
    def administer_reminders(self, medications, administers):
        container = pn.Column('# Today\'s medications')
        today = datetime.datetime.today()
        todays_administers = {
            'any':[],
            'morning':[],
            'mid-day':[],
            'night':[]}
        for i, administer in administers.iterrows():
            if administer['repeat'] == 'daily':
                todays_administers[administer['time']].append(administer)
            else:
                try:
                    if ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday').index(administer['repeat']) == today.weekday():
                        todays_administers[administer['time']].append(administer)
                except ValueError as error:
                    print(error)
                    pass
        if todays_administers['any'] != []:
            container.append(pn.pane.Markdown("## &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Any time"))
            for administer in todays_administers['any']:
                container.append(pn.Row(pn.pane.Markdown(f'## &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {administer["name"]}'), pn.widgets.Checkbox()))
        if todays_administers['morning'] != []:
            container.append(pn.pane.Markdown("## &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Morning"))
            for administer in todays_administers['morning']:
                container.append(pn.Row(pn.pane.Markdown(f'## &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {administer["name"]}'), pn.widgets.Checkbox()))
        if todays_administers['mid-day'] != []:
            container.append(pn.pane.Markdown("## &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Mid-day"))
            for administer in todays_administers['mid-day']:
                container.append(pn.Row(pn.pane.Markdown(f'## &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {administer["name"]}'), pn.widgets.Checkbox()))
        if todays_administers['night'] != []:
            container.append(pn.pane.Markdown("## &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Night"))
            for administer in todays_administers['night']:
                container.append(pn.Row(pn.pane.Markdown(f'## &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {administer["name"]}'), pn.widgets.Checkbox()))

        return container
    

app = App()