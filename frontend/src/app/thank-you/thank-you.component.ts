import { Component, Input } from '@angular/core';
import { TranslateDirective } from '@ngx-translate/core';

@Component({
    selector: 'wsl-thank-you',
    standalone: true,
    imports: [TranslateDirective],
    templateUrl: './thank-you.component.html',
    styleUrl: './thank-you.component.scss'
})
export class ThankYouComponent {
    @Input()
    firstName?: string;
}
