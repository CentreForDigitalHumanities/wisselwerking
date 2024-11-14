import { Component, Input } from '@angular/core';

@Component({
    selector: 'wsl-program-detail-line',
    standalone: true,
    imports: [],
    templateUrl: './program-detail-line.component.html',
    styleUrl: './program-detail-line.component.scss',
    host: { 'class': 'field is-horizontal' }
})
export class ProgramDetailLineComponent {
    @Input()
    label?: string;
}
