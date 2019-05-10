import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CanvasAspect } from '../../models';

@Component({
  selector: 'app-canvas-aspect-card-list',
  templateUrl: './canvas-aspect-card-list.component.html',
  styleUrls: ['./canvas-aspect-card-list.component.css']
})
export class CanvasAspectCardListComponent implements OnInit {

  @Input() canvasAspects: CanvasAspect[];

  @Output() add = new EventEmitter();

  constructor() { }

  ngOnInit() {
  }

}
