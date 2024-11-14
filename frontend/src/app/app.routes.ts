import { Routes } from '@angular/router';

import { OverviewComponent } from './overview/overview.component';
import { RegistrationComponent } from './registration/registration.component';

const routes: Routes = [
    {
        path: 'overview',
        component: OverviewComponent,
    },
    {
        path: 'registration',
        component: RegistrationComponent,
    },
    {
        path: '',
        redirectTo: '/overview',
        pathMatch: 'full'
    }
];

export { routes };
