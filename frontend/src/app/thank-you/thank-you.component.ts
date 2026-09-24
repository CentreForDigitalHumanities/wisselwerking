import { Component, Input } from '@angular/core';
import { TranslateDirective } from '@ngx-translate/core';

@Component({
    selector: 'wsl-thank-you',
    imports: [TranslateDirective],
    templateUrl: './thank-you.component.html',
    styleUrl: './thank-you.component.scss'
})
export class ThankYouComponent {
    @Input()
    firstName?: string;
}
