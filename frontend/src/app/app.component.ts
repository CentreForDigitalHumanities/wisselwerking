import { Component, Inject, afterRender } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import messagesNL from '../../locale/messages.nl.json';
import messagesEN from '../../locale/messages.en.json';
import { MenuComponent } from './menu/menu.component';
import { FooterComponent } from './footer/footer.component';
import { DarkModeService } from './services/dark-mode.service';

@Component({
    selector: 'wsl-root',
    standalone: true,
    imports: [RouterOutlet, MenuComponent, FooterComponent],
    templateUrl: './app.component.html',
    styleUrl: './app.component.scss'
})
export class AppComponent {
    title = 'Wisselwerking';

    constructor(@Inject(DOCUMENT) private document: Document,
        private darkModeService: DarkModeService,
        translate: TranslateService) {
        translate.setTranslation('nl', messagesNL);
        translate.setTranslation('en', messagesEN);
        translate.setFallbackLang('nl');

        // Using the DOM API to only render on the browser instead of on the server
        afterRender(() => {
            const style = this.document.createElement('link');
            style.rel = 'stylesheet';
            this.document.head.append(style);

            this.darkModeService.theme$.subscribe(theme => {
                this.document.documentElement.classList.remove(theme === 'dark' ? 'theme-light' : 'theme-dark');
                this.document.documentElement.classList.add('theme-' + theme);

                style.href = `${theme}.css`;
            });
        });
    }

}
